"""
Intent Classification Module
Classifies user query intent to determine response strategy.
"""

from typing import List
import re


class IntentClassifier:
    """Classifies query intent."""
    
    def __init__(self):
        """Initialize intent classifier with keyword patterns."""
        # Advisory keywords (investment advice)
        self.advisory_keywords = [
            'should i invest', 'should i buy', 'should i purchase',
            'is it good to invest', 'is it worth investing',
            'recommend', 'suggestion', 'advice',
            'best investment', 'good investment', 'bad investment'
        ]
        
        # Comparison keywords
        self.comparison_keywords = [
            'better than', 'vs', 'versus', 'compare',
            'which is better', 'which one is better',
            'difference between', 'compare with'
        ]
        
        # Prediction keywords
        self.prediction_keywords = [
            'will it go up', 'will it perform', 'future returns',
            'predict', 'forecast', 'will outperform',
            'future price', 'expected return'
        ]
        
        # Out-of-scope keywords (not mutual fund related)
        self.out_of_scope_keywords = [
            'gold', 'silver', 'commodity', 'commodities',
            'stock price', 'share price', 'equity price',
            'future', 'futures', 'options', 'option chain',
            'crude oil', 'natural gas', 'copper', 'zinc', 'nickel',
            'nifty 50', 'sensex', 'index', 'bank nifty',
            'bitcoin', 'crypto', 'cryptocurrency',
            'forex', 'currency', 'usd', 'eur', 'gbp'
        ]
        
        # Mutual fund specific keywords (must be present for in-scope queries)
        self.mutual_fund_keywords = [
            'fund', 'scheme', 'amc', 'nav', 'aum',
            'expense ratio', 'exit load', 'sip', 'swp',
            'elss', 'large cap', 'mid cap', 'small cap',
            'equity', 'debt', 'hybrid', 'balanced',
            'hdfc', 'icici', 'sbi', 'axis', 'kotak'
        ]
    
    def classify(self, query: str) -> str:
        """
        Classify query intent.
        
        Args:
            query: User query string
            
        Returns:
            Intent category: 'factual', 'advisory', 'comparison', 'prediction', 'out_of_scope'
        """
        query_lower = query.lower()
        
        # Check for out-of-scope first (gold, stocks, commodities, etc.)
        for keyword in self.out_of_scope_keywords:
            if keyword in query_lower:
                return 'out_of_scope'
        
        # Check for advisory intent
        for keyword in self.advisory_keywords:
            if keyword in query_lower:
                return 'advisory'
        
        # Check for comparison intent
        for keyword in self.comparison_keywords:
            if keyword in query_lower:
                return 'comparison'
        
        # Check for prediction intent
        for keyword in self.prediction_keywords:
            if keyword in query_lower:
                return 'prediction'
        
        # Default to factual
        return 'factual'
    
    def is_factual(self, query: str) -> bool:
        """
        Check if query is factual.
        
        Args:
            query: User query string
            
        Returns:
            True if factual, False otherwise
        """
        return self.classify(query) == 'factual'


if __name__ == "__main__":
    # Test intent classifier
    classifier = IntentClassifier()
    
    test_queries = [
        "What is the expense ratio?",
        "Should I invest in this fund?",
        "Which is better, HDFC or ICICI?",
        "Will this fund perform well next year?",
        "What are the top holdings?"
    ]
    
    for query in test_queries:
        intent = classifier.classify(query)
        print(f"Query: {query}")
        print(f"  Intent: {intent}")
        print(f"  Is factual: {classifier.is_factual(query)}")
        print()
