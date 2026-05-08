"""
Scraper Script
Fetches and stores data from corpus URLs using Phase 2.1 components.
"""

import sys
import os
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from http_client import HTTPClient
from html_parser import HTMLParser
from url_validator import URLValidator
from logger_config import LoggerConfig
from cache_manager import CacheManager
from error_handler import ErrorHandler


class WebScraper:
    """Main scraper class that coordinates all components."""
    
    def __init__(self, corpus_file: str, output_dir: str):
        """
        Initialize scraper.
        
        Args:
            corpus_file: Path to corpus URLs file
            output_dir: Directory to store scraped data
        """
        self.corpus_file = corpus_file
        self.output_dir = output_dir
        
        # Initialize components
        self.logger_config = LoggerConfig(log_level='INFO')
        self.logger = self.logger_config.setup_scraping_logger()
        self.cache = CacheManager(cache_dir=os.path.join(output_dir, 'cache'), ttl=86400)
        self.validator = URLValidator(timeout=10)
        self.error_handler = ErrorHandler(self.logger)
        
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create raw HTML directory
        self.raw_html_dir = os.path.join(output_dir, 'raw_html')
        if not os.path.exists(self.raw_html_dir):
            os.makedirs(self.raw_html_dir)
        
        # Create extracted text directory
        self.extracted_text_dir = os.path.join(output_dir, 'extracted_text')
        if not os.path.exists(self.extracted_text_dir):
            os.makedirs(self.extracted_text_dir)
        
        # Create metadata directory
        self.metadata_dir = os.path.join(output_dir, 'metadata')
        if not os.path.exists(self.metadata_dir):
            os.makedirs(self.metadata_dir)
    
    def read_corpus_urls(self) -> list:
        """
        Read URLs from corpus file.
        
        Returns:
            List of URLs
        """
        urls = []
        
        try:
            with open(self.corpus_file, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):
                        urls.append(url)
            
            self.logger.info(f"Read {len(urls)} URLs from corpus file")
            return urls
            
        except Exception as e:
            self.logger.error(f"Error reading corpus file: {str(e)}")
            raise
    
    def get_filename_from_url(self, url: str) -> str:
        """
        Generate filename from URL.
        
        Args:
            url: URL to generate filename from
            
        Returns:
            Filename
        """
        # Extract scheme name from URL
        # e.g., hdfc-large-cap-fund-direct-growth
        parts = url.split('/')
        scheme_name = parts[-1] if parts else 'unknown'
        
        # Remove special characters
        scheme_name = scheme_name.replace('-', '_')
        scheme_name = scheme_name.replace(' ', '_')
        
        return scheme_name
    
    def scrape_url(self, url: str) -> dict:
        """
        Scrape a single URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with scraping results
        """
        result = {
            'url': url,
            'success': False,
            'error': None,
            'timestamp': datetime.now().isoformat(),
            'raw_html_file': None,
            'extracted_text_file': None,
            'metadata_file': None
        }
        
        try:
            # Validate URL
            self.logger.info(f"Validating URL: {url}")
            validation = self.validator.validate_accessibility(url, method='HEAD')
            
            if not validation['accessible']:
                result['error'] = f"URL not accessible: {validation.get('error', 'Unknown error')}"
                self.logger.error(result['error'])
                return result
            
            self.logger.info(f"URL accessible. Status: {validation['status_code']}")
            
            # Check cache
            cached_content = self.cache.get(url)
            
            if cached_content:
                self.logger.info(f"Using cached content for {url}")
                html_content = cached_content
                result['from_cache'] = True
            else:
                # Fetch content
                self.logger.info(f"Fetching content from {url}")
                with HTTPClient(rate_limit_delay=2.0) as client:
                    response = client.get(url)
                    html_content = response.text
                    self.cache.set(url, html_content)
                    result['from_cache'] = False
                    self.logger.info(f"Fetched {len(html_content)} characters")
            
            # Save raw HTML
            filename = self.get_filename_from_url(url)
            raw_html_path = os.path.join(self.raw_html_dir, f"{filename}.html")
            
            with open(raw_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            result['raw_html_file'] = raw_html_path
            self.logger.info(f"Saved raw HTML to {raw_html_path}")
            
            # Parse HTML and extract text
            parser = HTMLParser()
            soup = parser.parse(html_content)
            
            # Extract text
            text = parser.extract_text(soup, remove_boilerplate=True)
            
            # Save extracted text
            extracted_text_path = os.path.join(self.extracted_text_dir, f"{filename}.txt")
            
            with open(extracted_text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            result['extracted_text_file'] = extracted_text_path
            result['text_length'] = len(text)
            self.logger.info(f"Saved extracted text to {extracted_text_path} ({len(text)} characters)")
            
            # Extract metadata
            metadata = parser.extract_metadata(soup)
            metadata.update({
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'status_code': validation['status_code'],
                'response_time': validation.get('response_time'),
                'text_length': len(text),
                'from_cache': result.get('from_cache', False)
            })
            
            # Save metadata
            metadata_path = os.path.join(self.metadata_dir, f"{filename}.json")
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            result['metadata_file'] = metadata_path
            result['metadata'] = metadata
            self.logger.info(f"Saved metadata to {metadata_path}")
            
            result['success'] = True
            self.logger.info(f"Successfully scraped {url}")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error scraping {url}: {str(e)}")
        
        return result
    
    def scrape_all(self) -> list:
        """
        Scrape all URLs from corpus.
        
        Returns:
            List of scraping results
        """
        urls = self.read_corpus_urls()
        results = []
        
        self.logger.info(f"Starting to scrape {len(urls)} URLs")
        
        for i, url in enumerate(urls, 1):
            self.logger.info(f"Processing URL {i}/{len(urls)}")
            result = self.scrape_url(url)
            results.append(result)
        
        # Save summary
        summary = {
            'total_urls': len(urls),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'from_cache': sum(1 for r in results if r.get('from_cache', False)),
            'scraped_at': datetime.now().isoformat(),
            'results': results
        }
        
        summary_path = os.path.join(self.output_dir, 'scraping_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Scraping summary saved to {summary_path}")
        self.logger.info(f"Scraping complete: {summary['successful']}/{summary['total_urls']} successful")
        
        return results


def main():
    """Main entry point."""
    # Configuration
    corpus_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'phase-1', '1.3-url-collection', 'corpus-urls.txt')
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scraped-data')
    
    print(f"Corpus file: {corpus_file}")
    print(f"Output directory: {output_dir}")
    
    # Create scraper
    scraper = WebScraper(corpus_file, output_dir)
    
    # Scrape all URLs
    results = scraper.scrape_all()
    
    # Print summary
    print("\n" + "="*50)
    print("SCRAPING SUMMARY")
    print("="*50)
    print(f"Total URLs: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    print(f"From Cache: {sum(1 for r in results if r.get('from_cache', False))}")
    print("="*50)
    
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['url']}")
        if not result['success']:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Text length: {result.get('text_length', 0)} characters")


if __name__ == "__main__":
    main()
