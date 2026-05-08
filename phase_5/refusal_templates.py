"""
Refusal Templates
Templates for refusal responses.
"""

REFUSAL_TEMPLATES = {
    'pii_block': "I cannot process queries containing personal information. Please remove any personal details (PAN, Aadhaar, phone number, email, OTP) and try again.",
    
    'dont_know': "I don't have information to answer this query. Please specify which mutual fund scheme you're asking about.",
    
    'advisory': "I can only provide factual information about mutual funds. I cannot provide investment advice or recommendations.",
    
    'comparison': "I can provide factual information about individual funds but cannot make comparisons or recommendations.",
    
    'prediction': "I can provide historical performance data but cannot predict future returns or performance.",
    
    'safe_template': "I'm unable to provide a specific answer at this time. Please check the official fund documents for accurate information."
}


def get_refusal_template(refusal_type: str, include_url: bool = False, url: str = None) -> str:
    """
    Get refusal template.
    
    Args:
        refusal_type: Type of refusal
        include_url: Whether to include URL
        url: URL to include
        
    Returns:
        Formatted refusal message
    """
    template = REFUSAL_TEMPLATES.get(refusal_type, REFUSAL_TEMPLATES['safe_template'])
    
    if include_url and url:
        template += f"\n\nSource: {url}"
    
    return template


if __name__ == "__main__":
    # Test refusal templates
    for refusal_type in REFUSAL_TEMPLATES.keys():
        print(f"{refusal_type}:")
        print(get_refusal_template(refusal_type))
        print()
