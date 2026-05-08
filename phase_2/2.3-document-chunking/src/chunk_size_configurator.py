"""
Chunk Size Configurator Module
Configures chunk size and overlap parameters.
"""

from typing import Dict, Any, Tuple, List


class ChunkSizeConfigurator:
    """Configurator for chunk size and overlap parameters."""
    
    def __init__(self):
        """Initialize chunk size configurator."""
        # Default configurations
        self.default_config = {
            'chunk_size': 800,  # tokens
            'overlap': 100,     # tokens
            'min_chunk_size': 100
        }
        
        # Preset configurations for different use cases
        self.presets = {
            'small_chunks': {
                'chunk_size': 500,
                'overlap': 50,
                'min_chunk_size': 50
            },
            'medium_chunks': {
                'chunk_size': 800,
                'overlap': 100,
                'min_chunk_size': 100
            },
            'large_chunks': {
                'chunk_size': 1000,
                'overlap': 150,
                'min_chunk_size': 150
            },
            'qa_focused': {
                'chunk_size': 600,
                'overlap': 75,
                'min_chunk_size': 75
            }
        }
    
    def get_config(self, preset: str = None) -> Dict[str, int]:
        """
        Get chunk configuration.
        
        Args:
            preset: Preset name (small_chunks, medium_chunks, large_chunks, qa_focused)
                   If None, returns default config
            
        Returns:
            Configuration dictionary
        """
        if preset and preset in self.presets:
            return self.presets[preset].copy()
        
        return self.default_config.copy()
    
    def create_custom_config(
        self,
        chunk_size: int,
        overlap: int,
        min_chunk_size: int = None
    ) -> Dict[str, int]:
        """
        Create custom chunk configuration.
        
        Args:
            chunk_size: Chunk size in tokens
            overlap: Overlap in tokens
            min_chunk_size: Minimum chunk size (defaults to chunk_size // 5)
            
        Returns:
            Configuration dictionary
        """
        if min_chunk_size is None:
            min_chunk_size = chunk_size // 5
        
        config = {
            'chunk_size': chunk_size,
            'overlap': overlap,
            'min_chunk_size': min_chunk_size
        }
        
        return config
    
    def validate_config(self, config: Dict[str, int]) -> Tuple[bool, List[str]]:
        """
        Validate chunk configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check required fields
        required_fields = ['chunk_size', 'overlap', 'min_chunk_size']
        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")
        
        # Validate chunk size
        if 'chunk_size' in config:
            if config['chunk_size'] < 100:
                issues.append("Chunk size too small (minimum: 100)")
            if config['chunk_size'] > 2000:
                issues.append("Chunk size too large (maximum: 2000)")
        
        # Validate overlap
        if 'overlap' in config:
            if config['overlap'] < 0:
                issues.append("Overlap cannot be negative")
            if config['overlap'] > config.get('chunk_size', 1000):
                issues.append("Overlap cannot be larger than chunk size")
        
        # Validate min_chunk_size
        if 'min_chunk_size' in config:
            if config['min_chunk_size'] < 10:
                issues.append("Min chunk size too small (minimum: 10)")
            if config['min_chunk_size'] > config.get('chunk_size', 1000):
                issues.append("Min chunk size cannot be larger than chunk size")
        
        is_valid = len(issues) == 0
        
        return is_valid, issues
    
    def recommend_config(self, text_length: int, use_case: str = 'general') -> Dict[str, int]:
        """
        Recommend configuration based on text length and use case.
        
        Args:
            text_length: Length of text to chunk
            use_case: Use case (general, qa, retrieval)
            
        Returns:
            Recommended configuration
        """
        # Base on text length
        if text_length < 1000:
            chunk_size = 300
            overlap = 50
        elif text_length < 5000:
            chunk_size = 500
            overlap = 75
        elif text_length < 20000:
            chunk_size = 800
            overlap = 100
        else:
            chunk_size = 1000
            overlap = 150
        
        # Adjust based on use case
        if use_case == 'qa':
            # Smaller chunks for Q&A
            chunk_size = int(chunk_size * 0.8)
            overlap = int(overlap * 0.8)
        elif use_case == 'retrieval':
            # Larger chunks for retrieval
            chunk_size = int(chunk_size * 1.2)
            overlap = int(overlap * 1.2)
        
        config = {
            'chunk_size': chunk_size,
            'overlap': overlap,
            'min_chunk_size': chunk_size // 5
        }
        
        return config
    
    def estimate_chunk_count(self, text_length: int, config: Dict[str, int]) -> int:
        """
        Estimate number of chunks for given text length and configuration.
        
        Args:
            text_length: Length of text
            config: Chunk configuration
            
        Returns:
            Estimated chunk count
        """
        chunk_size = config['chunk_size']
        overlap = config['overlap']
        
        effective_chunk_size = chunk_size - overlap
        
        if effective_chunk_size <= 0:
            return 1
        
        estimated_chunks = max(1, (text_length // effective_chunk_size) + 1)
        
        return estimated_chunks


if __name__ == "__main__":
    # Test the chunk size configurator
    configurator = ChunkSizeConfigurator()
    
    # Test presets
    print("Medium chunks preset:")
    print(configurator.get_config('medium_chunks'))
    
    # Test custom config
    print("\nCustom config:")
    custom = configurator.create_custom_config(chunk_size=600, overlap=80)
    print(custom)
    
    # Validate config
    is_valid, issues = configurator.validate_config(custom)
    print(f"\nValid: {is_valid}, Issues: {issues}")
    
    # Recommend config
    print("\nRecommended config for 10000 chars (QA):")
    recommended = configurator.recommend_config(10000, use_case='qa')
    print(recommended)
    
    # Estimate chunk count
    print(f"\nEstimated chunks for 10000 chars: {configurator.estimate_chunk_count(10000, recommended)}")
