"""
Content Extraction Pipeline
Processes scraped HTML files and outputs cleaned text with structure as JSON.
"""

import json
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_cleaner import TextCleaner
from noise_remover import NoiseRemover
from boilerplate_remover import BoilerplateRemover
from document_structure_preserver import DocumentStructurePreserver


class ContentExtractionPipeline:
    """Pipeline for extracting and cleaning content from HTML files."""
    
    def __init__(self):
        """Initialize the pipeline with all modules."""
        self.text_cleaner = TextCleaner()
        self.noise_remover = NoiseRemover()
        self.boilerplate_remover = BoilerplateRemover()
        self.structure_preserver = DocumentStructurePreserver()
    
    def process_html_file(self, html_path: str, output_path: str = None) -> dict:
        """
        Process a single HTML file.
        
        Args:
            html_path: Path to HTML file
            output_path: Path to save JSON output (optional)
            
        Returns:
            Dictionary with extracted content
        """
        # Read HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract scheme name from filename
        filename = Path(html_path).stem
        scheme_name = filename.replace('_', ' ').title()
        
        # Extract document structure from raw HTML
        structure = self.structure_preserver.extract_structure(html_content)
        
        # Format text with structure
        formatted_text = self.structure_preserver.format_text_with_structure(structure)
        
        # Remove boilerplate from formatted text
        cleaned_text = self.boilerplate_remover.remove_boilerplate(formatted_text, is_html=False)
        
        # Remove noise from text
        cleaned_text = self.noise_remover.remove_noise(cleaned_text)
        
        # Clean text
        final_text = self.text_cleaner.clean(cleaned_text)
        
        # Create output dictionary
        result = {
            'scheme_name': scheme_name,
            'source_file': str(html_path),
            'structure': structure,
            'cleaned_text': final_text,
            'statistics': {
                'original_size': len(html_content),
                'cleaned_size': len(final_text),
                'headings_count': len(structure['headings']),
                'paragraphs_count': len(structure['paragraphs']),
                'lists_count': len(structure['lists']),
                'tables_count': len(structure['tables'])
            }
        }
        
        # Save to JSON if output path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result
    
    def process_directory(
        self, 
        input_dir: str, 
        output_dir: str
    ) -> list:
        """
        Process all HTML files in a directory.
        
        Args:
            input_dir: Directory containing HTML files
            output_dir: Directory to save JSON outputs
            
        Returns:
            List of results
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = []
        
        # Process each HTML file
        for html_file in Path(input_dir).glob('*.html'):
            print(f"Processing: {html_file.name}")
            
            # Create output filename
            output_file = Path(output_dir) / f"{html_file.stem}.json"
            
            # Process file
            result = self.process_html_file(
                str(html_file),
                str(output_file)
            )
            
            results.append(result)
            print(f"  Saved: {output_file.name}")
            print(f"  Size: {result['statistics']['cleaned_size']} characters")
        
        return results


def main():
    """Main function to run the pipeline."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    raw_html_dir = base_dir / 'scraped-data' / 'raw_html'
    extracted_json_dir = base_dir / 'scraped-data' / 'extracted_json'
    
    print("=" * 60)
    print("Content Extraction Pipeline - Phase 2.2")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = ContentExtractionPipeline()
    
    # Process all HTML files
    print(f"\nInput directory: {raw_html_dir}")
    print(f"Output directory: {extracted_json_dir}\n")
    
    results = pipeline.process_directory(
        str(raw_html_dir),
        str(extracted_json_dir)
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("Processing Complete")
    print("=" * 60)
    print(f"Total files processed: {len(results)}")
    
    total_original = sum(r['statistics']['original_size'] for r in results)
    total_cleaned = sum(r['statistics']['cleaned_size'] for r in results)
    
    print(f"Total original size: {total_original:,} characters")
    print(f"Total cleaned size: {total_cleaned:,} characters")
    print(f"Reduction: {(1 - total_cleaned/total_original)*100:.1f}%")
    
    print(f"\nExtracted JSON files saved to: {extracted_json_dir}")


if __name__ == "__main__":
    main()
