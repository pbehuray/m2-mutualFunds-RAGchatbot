"""
Orchestrator Pipeline
End-to-end reasoning and guardrails orchestrator for Phase 5.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Load .env so GROQ_API_KEY is available when AnswerGenerator initialises
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=str(_env_path))
except ImportError:
    pass

# Add src paths
sys.path.append(os.path.join(os.path.dirname(__file__), '5.1-pii-detection', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '5.2-intent-classification', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '5.3-confidence-evaluator', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '5.4-answer-generation', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '5.5-url-policy-enforcer', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '5.6-post-processing-validator', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_4', '4.1-query-processing', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_4', '4.2-similarity-search', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase_4', '4.3-source-attribution', 'src'))
sys.path.append(os.path.dirname(__file__))

from pii_detector import PIIDetector
from intent_classifier import IntentClassifier
from confidence_evaluator import ConfidenceEvaluator
from answer_generator import AnswerGenerator
from url_policy_enforcer import URLPolicyEnforcer
from post_processing_validator import PostProcessingValidator
from refusal_templates import get_refusal_template

# Import Phase 4 components directly
from query_processor import QueryProcessor
from retriever import Retriever
from source_attributor import SourceAttributor


class Orchestrator:
    """
    Orchestrates the reasoning and guardrails pipeline.
    Decision flow: PII → Intent → Retrieval → Confidence → Generation → Post-Processing
    """
    
    def __init__(self, persist_directory: str = None, confidence_threshold: float = 0.6):
        """
        Initialize orchestrator.
        
        Args:
            persist_directory: Directory for vector database
            confidence_threshold: Minimum confidence threshold
        """
        self.pii_detector = PIIDetector()
        self.intent_classifier = IntentClassifier()
        self.confidence_evaluator = ConfidenceEvaluator(confidence_threshold)
        self.answer_generator = AnswerGenerator()
        self.url_enforcer = URLPolicyEnforcer()
        self.post_validator = PostProcessingValidator()
        
        # Phase 4 components
        self.query_processor = QueryProcessor()
        self.retriever = Retriever(persist_directory=persist_directory)
        self.source_attributor = SourceAttributor()
    
    def process_query(self, query: str, scheme: Optional[str] = None) -> Dict[str, Any]:
        """
        Process query through the orchestrator pipeline.
        
        Args:
            query: User query
            scheme: Optional scheme name to filter retrieval by
            
        Returns:
            Dictionary with response and metadata
        """
        # Step 1: PII Detection
        has_pii, pii_types = self.pii_detector.detect_pii(query)
        if has_pii:
            response = get_refusal_template('pii_block', include_url=False)
            return {
                'response': response,
                'route': 'pii_block',
                'pii_detected': True,
                'pii_types': pii_types,
                'include_url': False
            }
        
        # Step 2: Intent Classification
        intent = self.intent_classifier.classify(query)
        
        # Handle out-of-scope (gold, stocks, commodities, etc.) - NO URL
        if intent == 'out_of_scope':
            response = "I don't have information about that. I can only answer factual questions about HDFC Large Cap, Mid Cap, Equity, Focused, and ELSS Tax Saver mutual funds."
            return {
                'response': response,
                'route': 'refusal_out_of_scope',
                'intent': intent,
                'include_url': False
            }
        
        if intent != 'factual':
            # Non-factual intent (advisory/comparison/prediction) - return refusal with ONE whitelisted URL
            url = "https://groww.in/mutual-funds"
            response = get_refusal_template(intent, include_url=True, url=url)
            return {
                'response': response,
                'route': f'refusal_{intent}',
                'intent': intent,
                'include_url': True,
                'url': url
            }
        
        # Step 2.5: Fund Validation - only answer for funds we have in corpus
        available_funds = [
            'hdfc_large_cap', 'hdfc_largecap',
            'hdfc_mid_cap', 'hdfc_midcap',
            'hdfc_equity',
            'hdfc_focused',
            'hdfc_elss', 'hdfc_tax_saver'
        ]
        
        query_lower = query.lower()
        mentioned_fund = None
        for fund in available_funds:
            if fund.replace('_', ' ') in query_lower or fund in query_lower:
                mentioned_fund = fund
                break
        
        # If query mentions a fund we don't have, return don't know
        if mentioned_fund is None and any(word in query_lower for word in ['hdfc', 'fund', 'scheme']):
            # Check if it's a fund we DON'T have
            non_available_patterns = [
                'flexi cap', 'flexicap', 'small cap', 'smallcap',
                'balanced', 'hybrid', 'debt', 'liquid', 'gold',
                'nifty', 'index', 'etf', 'ppfas', 'parag',
                'quant', 'axis', 'icici', 'sbi', 'kotak', 'nippon'
            ]
            if any(pattern in query_lower for pattern in non_available_patterns):
                response = get_refusal_template('dont_know', include_url=False)
                return {
                    'response': response,
                    'route': 'dont_know',
                    'reason': 'fund_not_in_corpus',
                    'include_url': False
                }
        
        # Step 3: Retrieval
        query_info = self.query_processor.process_query(query)
        retrieval_results = self.retriever.search(
            query_info['normalized_query'],
            n_results=5,
            scheme_filter=scheme
        )
        
        # Step 4: Confidence Evaluation
        confidence_eval = self.confidence_evaluator.evaluate(retrieval_results)
        
        if not confidence_eval['has_results'] or not confidence_eval['meets_threshold']:
            # Don't know - return refusal with ZERO URLs
            response = get_refusal_template('dont_know', include_url=False)
            return {
                'response': response,
                'route': 'dont_know',
                'confidence': confidence_eval['top_score'],
                'include_url': False
            }
        
        # Step 5: Generate Answer — pass ALL retrieved chunks so Groq has full context
        response = self.answer_generator.generate(retrieval_results, query=query, include_url=True)

        # Step 6: Post-Processing Validation
        validation = self.post_validator.validate(response, require_url=True)
        
        if not validation['all_valid']:
            # Post-checks failed - use safe template with ONE whitelisted URL
            url = self.answer_generator.get_source_url(retrieval_results, query=query)
            response = get_refusal_template('safe_template', include_url=True, url=url)
            return {
                'response': response,
                'route': 'safe_fallback',
                'validation': validation,
                'include_url': True
            }
        
        # Success
        return {
            'response': response,
            'route': 'success',
            'confidence': confidence_eval['top_score'],
            'intent': intent,
            'validation': validation,
            'include_url': True
        }


def main():
    """Main function to test the orchestrator."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    persist_directory = str(base_dir / 'phase-3' / 'vector_db')
    
    print("=" * 60)
    print("Phase 5: Reasoning & Guardrails Orchestrator Test")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(persist_directory=persist_directory, confidence_threshold=0.6)
    
    # Test queries
    test_queries = [
        "What is the expense ratio?",
        "My PAN is ABCDE1234F, what should I invest?",
        "Should I invest in this fund?",
        "Which is better, HDFC or ICICI?",
        "Will this fund go up next year?",
        "What is the exit load?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        result = orchestrator.process_query(query)
        
        print(f"Route: {result['route']}")
        print(f"Include URL: {result.get('include_url', 'N/A')}")
        if 'confidence' in result:
            print(f"Confidence: {result['confidence']:.4f}")
        if 'intent' in result:
            print(f"Intent: {result['intent']}")
        if 'validation' in result:
            print(f"Validation: {result['validation']}")
        print(f"\nResponse:\n{result['response']}")


if __name__ == "__main__":
    main()
