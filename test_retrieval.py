import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'phase_4/4.1-query-processing/src')
sys.path.insert(0, 'phase_4/4.2-similarity-search/src')
sys.path.insert(0, 'phase_4/4.3-source-attribution/src')
sys.path.insert(0, 'phase_3/3.2-vector-database-setup/src')
sys.path.insert(0, 'phase_3/3.3-embedding-generation/src')

from query_processor import QueryProcessor
from retriever import Retriever

qp = QueryProcessor()
r = Retriever(persist_directory='phase_3/3.2-vector-database-setup/chroma_db')

query = 'what is NAV of hdfc large cap fund'
results = r.search(query, n_results=5)

print('Top results for:', query)
for i, res in enumerate(results):
    score = res.get('score', 'N/A')
    text = res.get('text', '')[:500]
    meta = res.get('metadata', {})
    print(f'\n--- Result {i+1} (score: {score}) ---')
    print(text)
    print('Metadata:', meta)
