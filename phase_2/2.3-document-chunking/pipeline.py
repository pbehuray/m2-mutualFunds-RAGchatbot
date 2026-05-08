"""
Document Chunking Pipeline
Processes extracted JSON files and generates chunks with metadata.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from semantic_chunker import SemanticChunker, Chunk
from metadata_tagger import MetadataTagger
from chunk_validator import ChunkValidator
from chunk_size_configurator import ChunkSizeConfigurator


class ChunkingPipeline:
    """Pipeline for chunking documents with metadata and validation."""
    
    def __init__(self):
        """Initialize the pipeline with all modules."""
        self.configurator = ChunkSizeConfigurator()
        self.chunker = SemanticChunker()
        self.tagger = MetadataTagger()
        self.validator = ChunkValidator()
    
    def process_json_file(self, json_path: str, output_path: str = None) -> dict:
        """
        Process a single JSON file and generate chunks.
        
        Args:
            json_path: Path to JSON file
            output_path: Path to save chunked output (optional)
            
        Returns:
            Dictionary with chunks and metadata
        """
        # Read JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cleaned_text = data.get('cleaned_text', '')
        scheme_name = data.get('scheme_name', '')
        source_file = data.get('source_file', '')
        
        # Get chunk configuration
        config = self.configurator.get_config('medium_chunks')
        
        # Update chunker with config
        self.chunker.chunk_size = config['chunk_size']
        self.chunker.overlap = config['overlap']
        self.chunker.min_chunk_size = config['min_chunk_size']
        
        # Create base metadata
        base_metadata = {
            'scheme_name': scheme_name,
            'source_file': source_file,
            'chunk_size_config': config
        }
        
        # Chunk the text
        chunks = self.chunker.chunk_by_sections(cleaned_text, base_metadata)
        
        # Add enhanced metadata to each chunk
        for i, chunk in enumerate(chunks):
            # Add base metadata
            chunk.metadata = self.tagger.tag_chunk(
                chunk.text,
                base_metadata=chunk.metadata,
                chunk_index=i,
                total_chunks=len(chunks)
            )
            
            # Add source metadata
            chunk.metadata = self.tagger.add_source_metadata(
                chunk.metadata,
                source_url=source_file,
                scheme_name=scheme_name,
                document_type='json'
            )
            
            # Add content metadata
            chunk.metadata = self.tagger.add_content_metadata(chunk.metadata, chunk.text)
            
            # Create unique chunk ID
            chunk.metadata['chunk_id'] = self.tagger.create_chunk_id(
                scheme_name,
                i,
                chunk.metadata.get('chunk_type', 'section')
            )
        
        # Validate chunks
        validation_results = []
        for chunk in chunks:
            is_valid, issues = self.validator.validate_chunk(chunk.text)
            quality_score = self.validator.get_quality_score(chunk.text)
            
            validation_results.append({
                'chunk_id': chunk.metadata['chunk_id'],
                'is_valid': is_valid,
                'issues': issues,
                'quality_score': quality_score
            })
            
            # Add validation results to chunk metadata
            chunk.metadata['validation'] = {
                'is_valid': is_valid,
                'quality_score': quality_score
            }
        
        # Convert chunks to serializable format
        chunks_serializable = []
        for chunk in chunks:
            chunks_serializable.append({
                'text': chunk.text,
                'metadata': chunk.metadata,
                'start_position': chunk.start_position,
                'end_position': chunk.end_position
            })
        
        # Create output dictionary
        result = {
            'scheme_name': scheme_name,
            'source_file': source_file,
            'chunk_config': config,
            'total_chunks': len(chunks),
            'chunks': chunks_serializable,
            'validation_summary': {
                'total_chunks': len(chunks),
                'valid_chunks': sum(1 for v in validation_results if v['is_valid']),
                'invalid_chunks': sum(1 for v in validation_results if not v['is_valid']),
                'average_quality_score': sum(v['quality_score'] for v in validation_results) / len(validation_results) if validation_results else 0
            },
            'validation_results': validation_results
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
    ) -> List[Dict[str, Any]]:
        """
        Process all JSON files in a directory.
        
        Args:
            input_dir: Directory containing JSON files
            output_dir: Directory to save chunked outputs
            
        Returns:
            List of results
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = []
        
        # Process each JSON file
        for json_file in Path(input_dir).glob('*.json'):
            print(f"Processing: {json_file.name}")
            
            # Create output filename
            output_file = Path(output_dir) / f"{json_file.stem}_chunked.json"
            
            # Process file
            result = self.process_json_file(
                str(json_file),
                str(output_file)
            )
            
            results.append(result)
            print(f"  Saved: {output_file.name}")
            print(f"  Chunks: {result['total_chunks']}")
            print(f"  Valid chunks: {result['validation_summary']['valid_chunks']}")
            print(f"  Avg quality: {result['validation_summary']['average_quality_score']:.2f}")
        
        return results


def main():
    """Main function to run the pipeline."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    extracted_json_dir = base_dir / 'scraped-data' / 'extracted_json'
    chunked_json_dir = base_dir / 'scraped-data' / 'chunked_json'
    
    print("=" * 60)
    print("Document Chunking Pipeline - Phase 2.3")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = ChunkingPipeline()
    
    # Process all JSON files
    print(f"\nInput directory: {extracted_json_dir}")
    print(f"Output directory: {chunked_json_dir}\n")
    
    results = pipeline.process_directory(
        str(extracted_json_dir),
        str(chunked_json_dir)
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("Processing Complete")
    print("=" * 60)
    print(f"Total files processed: {len(results)}")
    
    total_chunks = sum(r['total_chunks'] for r in results)
    total_valid = sum(r['validation_summary']['valid_chunks'] for r in results)
    total_invalid = sum(r['validation_summary']['invalid_chunks'] for r in results)
    avg_quality = sum(r['validation_summary']['average_quality_score'] for r in results) / len(results)
    
    print(f"Total chunks generated: {total_chunks}")
    print(f"Valid chunks: {total_valid}")
    print(f"Invalid chunks: {total_invalid}")
    print(f"Average quality score: {avg_quality:.2f}")
    
    print(f"\nChunked JSON files saved to: {chunked_json_dir}")


if __name__ == "__main__":
    main()
