"""
Confidence Evaluator Module
Evaluates confidence of retrieval results.
"""

from typing import Dict, Any, List


class ConfidenceEvaluator:
    """Evaluates confidence of retrieval results."""
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize confidence evaluator.
        
        Args:
            confidence_threshold: Minimum similarity score threshold
        """
        self.confidence_threshold = confidence_threshold
    
    def evaluate(self, retrieval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate confidence of retrieval results.
        
        Args:
            retrieval_results: List of retrieval results with similarity scores
            
        Returns:
            Dictionary with confidence evaluation
        """
        if not retrieval_results:
            return {
                'has_results': False,
                'confidence': 0.0,
                'meets_threshold': False,
                'top_score': 0.0
            }
        
        top_score = retrieval_results[0].get('similarity_score', 0.0)
        has_results = len(retrieval_results) > 0
        meets_threshold = top_score >= self.confidence_threshold
        
        return {
            'has_results': has_results,
            'confidence': top_score,
            'meets_threshold': meets_threshold,
            'top_score': top_score
        }
    
    def should_answer(self, retrieval_results: List[Dict[str, Any]]) -> bool:
        """
        Determine if we should answer based on confidence.
        
        Args:
            retrieval_results: List of retrieval results
            
        Returns:
            True if should answer, False otherwise
        """
        evaluation = self.evaluate(retrieval_results)
        return evaluation['has_results'] and evaluation['meets_threshold']


if __name__ == "__main__":
    # Test confidence evaluator
    evaluator = ConfidenceEvaluator(confidence_threshold=0.6)
    
    test_results = [
        [{'similarity_score': 0.85, 'text': 'test'}],
        [{'similarity_score': 0.5, 'text': 'test'}],
        []
    ]
    
    for results in test_results:
        evaluation = evaluator.evaluate(results)
        should_answer = evaluator.should_answer(results)
        print(f"Results: {results}")
        print(f"  Evaluation: {evaluation}")
        print(f"  Should answer: {should_answer}")
        print()
