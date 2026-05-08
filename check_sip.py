import sys, re
sys.path.insert(0, 'c:/milestone 2')
from phase_6.api.main import (
    _looks_like_scheme_facts_query,
    _looks_like_nav_query,
    _looks_like_expense_ratio_query,
    _should_refuse_out_of_scope,
    _groww_url_for_query,
)
from phase_6.api.scheme_facts_service import SchemeFactsClient

client = SchemeFactsClient(workspace_root='c:/milestone 2')

queries = [
    'what is min sip for hdfc focused fund direct growth',
    'minimum sip for hdfc focused fund',
    'what is minimum SIP for hdfc focused fund',
    'min sip hdfc focused',
    'what is the minimum SIP amount for hdfc focused fund',
]

for q in queries:
    refused = _should_refuse_out_of_scope(q, None)
    is_nav = _looks_like_nav_query(q)
    is_exp = _looks_like_expense_ratio_query(q)
    is_facts = _looks_like_scheme_facts_query(q)
    facts = client.get_facts('hdfc focused fund')

    # Simulate the facts handler
    answer = None
    if facts and is_facts:
        ql = q.lower()
        if 'sip' in ql:
            answer = f"Minimum SIP amount for {facts.matched_scheme} is {facts.min_sip}." if facts.min_sip else "Not found"

    print(f'Q: {q}')
    print(f'  refused={refused}, nav={is_nav}, expense={is_exp}, facts={is_facts}')
    print(f'  min_sip from facts: {facts.min_sip if facts else "NO FACTS"}')
    print(f'  simulated answer: {answer}')
    print()
