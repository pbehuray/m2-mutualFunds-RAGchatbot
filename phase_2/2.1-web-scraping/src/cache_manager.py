"""
Cache Manager Module
Manages caching for web scraping operations to avoid redundant requests.
"""

import hashlib
import json
import os
import time
from typing import Optional, Any, Dict
import pickle


class CacheManager:
    """Cache manager for storing and retrieving scraped content."""
    
    def __init__(
        self,
        cache_dir: str = 'cache',
        ttl: int = 86400,  # 24 hours in seconds
        use_compression: bool = False
    ):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files
            ttl: Time to live for cache entries in seconds
            use_compression: Whether to compress cache entries
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.use_compression = use_compression
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, url: str) -> str:
        """
        Generate cache key from URL.
        
        Args:
            url: URL to generate key for
            
        Returns:
            Cache key (hash of URL)
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """
        Get file path for cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            File path for cache entry
        """
        return os.path.join(self.cache_dir, f"{key}.cache")
    
    def _get_metadata_path(self, key: str) -> str:
        """
        Get file path for cache metadata.
        
        Args:
            key: Cache key
            
        Returns:
            File path for metadata
        """
        return os.path.join(self.cache_dir, f"{key}.meta")
    
    def get(self, url: str) -> Optional[Any]:
        """
        Get cached content for URL.
        
        Args:
            url: URL to retrieve from cache
            
        Returns:
            Cached content if available and not expired, None otherwise
        """
        key = self._get_cache_key(url)
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)
        
        # Check if cache entry exists
        if not os.path.exists(cache_path) or not os.path.exists(meta_path):
            return None
        
        # Check if cache entry is expired
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            cache_time = metadata.get('timestamp', 0)
            if time.time() - cache_time > self.ttl:
                # Cache expired, delete it
                self.delete(url)
                return None
        except Exception as e:
            # Metadata corrupted, delete cache
            self.delete(url)
            return None
        
        # Load cached content
        try:
            with open(cache_path, 'rb') as f:
                content = pickle.load(f)
            return content
        except Exception as e:
            # Cache corrupted, delete it
            self.delete(url)
            return None
    
    def set(self, url: str, content: Any) -> bool:
        """
        Cache content for URL.
        
        Args:
            url: URL to cache
            content: Content to cache
            
        Returns:
            True if successful, False otherwise
        """
        key = self._get_cache_key(url)
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)
        
        try:
            # Save content
            with open(cache_path, 'wb') as f:
                pickle.dump(content, f)
            
            # Save metadata
            metadata = {
                'url': url,
                'timestamp': time.time(),
                'ttl': self.ttl,
                'size': os.path.getsize(cache_path)
            }
            
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
        except Exception as e:
            # If saving fails, clean up
            if os.path.exists(cache_path):
                os.remove(cache_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
            return False
    
    def delete(self, url: str) -> bool:
        """
        Delete cached content for URL.
        
        Args:
            url: URL to delete from cache
            
        Returns:
            True if successful, False otherwise
        """
        key = self._get_cache_key(url)
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(key)
        
        success = True
        
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except Exception:
                success = False
        
        if os.path.exists(meta_path):
            try:
                os.remove(meta_path)
            except Exception:
                success = False
        
        return success
    
    def clear(self) -> bool:
        """
        Clear all cached content.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            'total_entries': 0,
            'total_size': 0,
            'expired_entries': 0,
            'cache_dir': self.cache_dir
        }
        
        try:
            current_time = time.time()
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.meta'):
                    meta_path = os.path.join(self.cache_dir, filename)
                    
                    try:
                        with open(meta_path, 'r') as f:
                            metadata = json.load(f)
                        
                        stats['total_entries'] += 1
                        stats['total_size'] += metadata.get('size', 0)
                        
                        if current_time - metadata.get('timestamp', 0) > self.ttl:
                            stats['expired_entries'] += 1
                    except Exception:
                        pass
        except Exception:
            pass
        
        return stats
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        removed_count = 0
        current_time = time.time()
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.meta'):
                    meta_path = os.path.join(self.cache_dir, filename)
                    
                    try:
                        with open(meta_path, 'r') as f:
                            metadata = json.load(f)
                        
                        if current_time - metadata.get('timestamp', 0) > self.ttl:
                            # Get URL from metadata
                            url = metadata.get('url')
                            if url:
                                if self.delete(url):
                                    removed_count += 1
                    except Exception:
                        pass
        except Exception:
            pass
        
        return removed_count


if __name__ == "__main__":
    # Test the cache manager
    cache = CacheManager(cache_dir='test_cache', ttl=60)
    
    # Test cache operations
    test_url = "https://example.com/test"
    test_content = {"data": "test content", "timestamp": time.time()}
    
    print("Testing cache operations:")
    
    # Set cache
    print(f"Setting cache for {test_url}")
    success = cache.set(test_url, test_content)
    print(f"Cache set: {success}")
    
    # Get cache
    print(f"\nGetting cache for {test_url}")
    cached_content = cache.get(test_url)
    print(f"Cached content: {cached_content}")
    
    # Get stats
    print(f"\nCache stats:")
    stats = cache.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Cleanup
    print(f"\nCleaning up expired entries:")
    removed = cache.cleanup_expired()
    print(f"Removed {removed} expired entries")
    
    # Clear cache
    print(f"\nClearing cache:")
    cache.clear()
    print("Cache cleared")
    
    # Clean up test directory
    import shutil
    if os.path.exists('test_cache'):
        shutil.rmtree('test_cache')
