"""
Improved Document Chunker
Preserves key metrics (AUM, expense ratio, SIP, etc.) by using semantic chunking.
"""

import json
import re
from typing import List, Dict, Any
from pathlib import Path


class ImprovedChunker:
    """Chunker that preserves key fund metrics."""
    
    def __init__(self):
        self.key_patterns = [
            r'Fund size.*?AUM.*?Cr',
            r'Expense ratio.*?\d+\.\d+%',
            r'Min\. for SIP.*?₹\d+',
            r'NAV.*?₹[\d,]+\.?\d*',
            r'Exit load',
            r'Riskometer',
            r'Benchmark',
            r'Lock-in',
            r'Category',
            r'Rating'
        ]
    
    def extract_key_metrics(self, text: str) -> Dict[str, str]:
        """Extract key metrics from text."""
        metrics = {}
        
        # AUM - matches "Fund size (AUM) ₹35,458.50 Cr"
        aum_match = re.search(r'Fund size\s*\(AUM\)\s*₹[\d,.]+\s*Cr', text, re.IGNORECASE)
        if aum_match:
            metrics['aum'] = aum_match.group(0)
        
        # Expense ratio - matches "Expense ratio 1.04%"
        expense_match = re.search(r'Expense ratio\s*\d+\.\d+%', text, re.IGNORECASE)
        if expense_match:
            metrics['expense_ratio'] = expense_match.group(0)
        
        # SIP - matches "Min. for SIP ₹100"
        sip_match = re.search(r'Min\.?\s*for\s*SIP\s*₹\d+', text, re.IGNORECASE)
        if sip_match:
            metrics['min_sip'] = sip_match.group(0)
        
        # NAV - matches "NAV: 04 May 26 ₹1,192.37"
        nav_match = re.search(r'NAV:?\s*[\d\w\s]+₹[\d,]+\.?\d*', text, re.IGNORECASE)
        if nav_match:
            metrics['nav'] = nav_match.group(0)
        
        # Exit load - matches "Exit load" or "Exit load: Nil"
        exit_load_match = re.search(r'Exit load:?\s*(?:\d+\.\d+%|Nil|0\.0%|0%)', text, re.IGNORECASE)
        if exit_load_match:
            metrics['exit_load'] = exit_load_match.group(0)
        
        # Riskometer - matches "Riskometer" with level
        risk_match = re.search(r'Riskometer.*?(?:High|Moderate|Low|Very High)', text, re.IGNORECASE)
        if risk_match:
            metrics['riskometer'] = risk_match.group(0)
        
        # Benchmark - matches "Benchmark" with index name
        benchmark_match = re.search(r'Benchmark:?\s*[A-Z][A-Za-z\s]+(?:Index)?', text, re.IGNORECASE)
        if benchmark_match:
            metrics['benchmark'] = benchmark_match.group(0)
        
        return metrics
    
    def chunk_document(self, text: str, scheme_name: str, source_file: str) -> Dict[str, Any]:
        """Chunk document while preserving key metrics."""
        chunks = []
        
        # Extract key metrics
        metrics = self.extract_key_metrics(text)
        
        # Create a metrics chunk (always first chunk)
        if metrics:
            metrics_text = f"Key Metrics for {scheme_name}\n\n"
            for key, value in metrics.items():
                clean_value = value.strip()
                metrics_text += f"{key.replace('_', ' ').title()}: {clean_value}\n"
            
            chunks.append({
                "text": metrics_text,
                "metadata": {
                    "scheme_name": scheme_name,
                    "source_file": source_file,
                    "chunk_type": "key_metrics",
                    "chunk_id": f"{scheme_name.replace(' ', '_').lower()}_metrics"
                }
            })
        
        # Split text into sections based on headers
        sections = re.split(r'\n\n+', text)
        
        # Chunk each section
        chunk_size = 1000
        overlap = 100
        
        for i, section in enumerate(sections):
            if len(section.strip()) < 50:
                continue
            
            # If section is short, keep as is
            if len(section) <= chunk_size:
                chunks.append({
                    "text": section,
                    "metadata": {
                        "scheme_name": scheme_name,
                        "source_file": source_file,
                        "chunk_type": "section",
                        "section_index": i,
                        "chunk_id": f"{scheme_name.replace(' ', '_').lower()}_section_{i}"
                    }
                })
            else:
                # Split long sections with overlap
                for j in range(0, len(section), chunk_size - overlap):
                    chunk_text = section[j:j + chunk_size]
                    if len(chunk_text.strip()) < 50:
                        continue
                    
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "scheme_name": scheme_name,
                            "source_file": source_file,
                            "chunk_type": "section_chunk",
                            "section_index": i,
                            "chunk_index": j // (chunk_size - overlap),
                            "chunk_id": f"{scheme_name.replace(' ', '_').lower()}_section_{i}_chunk_{j // (chunk_size - overlap)}"
                        }
                    })
        
        return {
            "scheme_name": scheme_name,
            "source_file": source_file,
            "total_chunks": len(chunks),
            "chunks": chunks,
            "key_metrics": metrics
        }


def rechunk_all():
    """Re-chunk all extracted texts with improved strategy."""
    extracted_dir = Path("phase_2/scraped-data/extracted_text")
    chunked_dir = Path("phase_2/scraped-data/chunked_json")
    chunked_dir.mkdir(parents=True, exist_ok=True)
    
    chunker = ImprovedChunker()
    
    for txt_file in extracted_dir.glob("*.txt"):
        scheme_name = txt_file.stem.replace("_", " ").title()
        source_file = str(txt_file).replace("\\", "/")
        
        print(f"Processing {scheme_name}...")
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        chunked = chunker.chunk_document(text, scheme_name, source_file)
        
        output_file = chunked_dir / f"{txt_file.stem}_chunked.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunked, f, indent=2)
        
        print(f"  Created {chunked['total_chunks']} chunks")
        print(f"  Key metrics found: {list(chunked['key_metrics'].keys())}")
        print()


if __name__ == "__main__":
    rechunk_all()
