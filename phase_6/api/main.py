"""
FastAPI application for Phase 6: API Layer.
"""

import os
import sys
import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime

# Load .env before anything else
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))
except ImportError:
    pass  # dotenv not installed; rely on environment variables being set externally

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from phase_6.api.models import (
    QueryRequest,
    QueryResponse,
    SchemesResponse,
    HealthResponse,
    FeedbackRequest,
    FeedbackResponse,
    SchemeInfo,
    NavResponse,
)
from phase_6.api.rate_limiter import check_rate_limit
from phase_6.api.cache import get_cache, generate_cache_key
from phase_6.api.nav_service import AmfiNavClient, AMFI_NAVALL_URL
from phase_6.api.expense_ratio_service import ExpenseRatioClient
from phase_6.api.scheme_facts_service import SchemeFactsClient
from phase_5.orchestrator import Orchestrator

# Initialize FastAPI app
app = FastAPI(
    title="Mutual Fund FAQ Assistant API",
    description="Facts-only Q&A assistant for mutual fund schemes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'phase_7', 'frontend')
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Initialize orchestrator and cache
orchestrator = None
cache = None
nav_client = AmfiNavClient()
expense_ratio_client = ExpenseRatioClient(workspace_root=project_root)
scheme_facts_client = SchemeFactsClient(workspace_root=project_root)

SUPPORTED_FUND_ALIASES = [
    "hdfc large cap",
    "hdfc largecap",
    "hdfc large cap fund",
    "hdfc mid cap",
    "hdfc midcap",
    "hdfc mid cap fund",
    "hdfc equity",
    "hdfc equity fund",
    "hdfc flexi cap",
    "hdfc flexi cap fund",
    "hdfc focused",
    "hdfc focused fund",
    "hdfc elss",
    "hdfc tax saver",
    "hdfc elss tax saver",
    "hdfc elss tax saver fund",
]

OUT_OF_SCOPE_MARKET_TERMS = [
    "stock",
    "stocks",
    "stock price",
    "share",
    "share price",
    "gold",
    "silver",
    "commodity",
    "commodities",
    "future",
    "futures",
    "option",
    "options",
    "option chain",
    "mcx",
    "crude oil",
    "natural gas",
    "copper",
    "zinc",
    "nickel",
    "nifty",
    "nifty 50",
    "sensex",
    "bank nifty",
    "bitcoin",
    "crypto",
    "cryptocurrency",
    "forex",
    "currency",
]

UNSUPPORTED_FUND_TERMS = [
    "flexi cap",
    "flexicap",
    "small cap",
    "smallcap",
    "balanced",
    "hybrid",
    "debt",
    "liquid",
    "index fund",
    "etf",
    "ppfas",
    "parag",
    "quant",
    "axis",
    "icici",
    "sbi",
    "kotak",
    "nippon",
]

SCOPE_REFUSAL = (
    "I don't have information about that. I can only answer factual questions "
    "about HDFC Large Cap, Mid Cap, Equity, Focused, and ELSS Tax Saver mutual funds."
)


def _normalize_scope_text(value: Optional[str]) -> str:
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return f" {' '.join(value.split())} "


def _has_scope_term(text: str, terms: List[str]) -> bool:
    return any(f" {term} " in text for term in terms)


def _mentions_supported_fund(query: str, scheme: Optional[str]) -> bool:
    combined = _normalize_scope_text(f"{query or ''} {scheme or ''}")
    return _has_scope_term(combined, SUPPORTED_FUND_ALIASES)


def _should_refuse_out_of_scope(query: str, scheme: Optional[str]) -> bool:
    query_text = _normalize_scope_text(query)
    scheme_text = _normalize_scope_text(scheme)
    combined_text = _normalize_scope_text(f"{query or ''} {scheme or ''}")

    if _mentions_supported_fund(query, scheme):
        return False

    if scheme and not _has_scope_term(scheme_text, SUPPORTED_FUND_ALIASES):
        return True

    if _has_scope_term(query_text, OUT_OF_SCOPE_MARKET_TERMS):
        return True

    if _has_scope_term(combined_text, UNSUPPORTED_FUND_TERMS):
        return True

    mentions_generic_fund = _has_scope_term(combined_text, ["fund", "scheme", "mutual fund"])
    mentions_hdfc = _has_scope_term(combined_text, ["hdfc"])
    return mentions_generic_fund and mentions_hdfc


def _groww_url_for_scheme(scheme_name: str) -> str:
    """Map a matched AMFI scheme name or file-stem to its Groww corpus URL."""
    s = (scheme_name or "").lower()
    if "large cap" in s or "largecap" in s:
        return "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    if "mid cap" in s or "midcap" in s:
        return "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    if "focused" in s:
        return "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth"
    if "elss" in s or "tax saver" in s or "tax_saver" in s:
        return "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"
    # equity / flexi cap — must come after the more specific checks above
    if "equity" in s or "flexi cap" in s or "flexi_cap" in s:
        return "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"
    return "https://groww.in/mutual-funds"


def _groww_url_for_query(query: str, scheme: Optional[str] = None) -> str:
    """Derive the correct Groww URL from a free-text query + optional scheme hint."""
    combined = (f"{query or ''} {scheme or ''}").lower()
    if "large cap" in combined or "largecap" in combined:
        return "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
    if "mid cap" in combined or "midcap" in combined:
        return "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    if "focused" in combined:
        return "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth"
    if "elss" in combined or "tax saver" in combined:
        return "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"
    if "equity" in combined or "flexi cap" in combined:
        return "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"
    return "https://groww.in/mutual-funds"


def _out_of_scope_response(request: QueryRequest) -> QueryResponse:
    return QueryResponse(
        answer=SCOPE_REFUSAL,
        source="",
        scheme=request.scheme,
        confidence=0.0,
        route="refusal_out_of_scope",
        include_url=False,
    )


def _looks_like_nav_query(q: str) -> bool:
    q = (q or "").lower()
    return bool(re.search(r"\bnav\b", q)) or ("net asset value" in q)


def _looks_like_expense_ratio_query(q: str) -> bool:
    q = (q or "").lower()
    return (
        bool(re.search(r"\bter\b", q))
        or bool(re.search(r"\bexp(?:e|en)se\s+rat(?:io|ion)\b", q))
        or bool(re.search(r"\bexp(?:e|en)se\b.{0,20}\bratio\b", q))
    )


def _looks_like_scheme_facts_query(q: str) -> bool:
    q = (q or "").lower()
    triggers = [
        "exit load",
        "minimum sip",
        "min sip",
        "minimum lumpsum",
        "riskometer",
        "risk",
        "benchmark",
        "lock in",
        "lock-in",
        "aum",
        "assets under management",
        "asset under management",
        "fund manager",
        "who manages",
        "managed by",
        "manager of",
    ]
    q_words = set(q.split())
    for t in triggers:
        if t in q:
            return True
        # For multi-word triggers, also match when all words appear anywhere in the query
        t_words = t.split()
        if len(t_words) > 1 and all(w in q_words for w in t_words):
            return True
    return False


def _fact_answer(label: str, scheme: str, value: Optional[str]) -> tuple[str, float]:
    if value:
        return f"{label} for {scheme} is {value}.", 1.0
    return f"I couldn't extract {label.lower()} for {scheme} from the local sources.", 0.0


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator and cache on startup."""
    global orchestrator, cache
    try:
        persist_directory = os.path.join(project_root, "phase_3", "vector_db")
        orchestrator = Orchestrator(persist_directory=persist_directory)
        print("Orchestrator initialized successfully")
    except Exception as e:
        print(f"Error initializing orchestrator: {e}")
        orchestrator = None
    
    try:
        cache = get_cache()
        print("Cache initialized successfully")
    except Exception as e:
        print(f"Error initializing cache: {e}")
        cache = None


@app.get("/")
async def root():
    """Serve the frontend index.html."""
    index_path = os.path.join(frontend_dir, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Mutual Fund FAQ Assistant API", "docs": "/docs"}


@app.get("/api/nav", response_model=NavResponse)
async def get_nav(scheme: str):
    """Return latest NAV for a scheme from AMFI."""
    best, score = nav_client.find_best_match(scheme)
    if not best or score < 0.55:
        return NavResponse(
            scheme=scheme,
            matched_scheme=best.scheme_name if best else None,
            nav=None,
            nav_date=None,
            source_url=AMFI_NAVALL_URL,
            note="NAV not found with sufficient confidence. Try the exact scheme variant (Direct/Regular + Growth/IDCWs).",
        )

    try:
        nav_value = float(best.nav)
    except Exception:
        nav_value = None

    return NavResponse(
        scheme=scheme,
        matched_scheme=best.scheme_name,
        nav=nav_value,
        nav_date=best.nav_date,
        source_url=_groww_url_for_scheme(best.scheme_name),
        note=None,
    )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        orchestrator_ready=orchestrator is not None
    )


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, http_request: Request):
    """
    Submit a query and get response.
    
    Args:
        request: QueryRequest with query and optional scheme
        http_request: FastAPI request for rate limiting
        
    Returns:
        QueryResponse with answer, source, and metadata
    """
    # Check rate limit
    await check_rate_limit(http_request)
    
    cache_key = generate_cache_key(request.query, request.scheme)

    # Enforce the five-fund scope before cache and specialized lookup paths.
    if _should_refuse_out_of_scope(request.query, request.scheme):
        response = _out_of_scope_response(request)
        if cache:
            cache.set(cache_key, response.dict(), ttl=3600)
        return response

    # Check cache after scope enforcement so stale broad-market answers cannot leak.
    if cache:
        cached_response = cache.get(cache_key)
        if cached_response:
            print(f"Cache hit for query: {request.query}")
            return QueryResponse(**cached_response)

    # NAV queries: use AMFI feed instead of scraped corpus
    if _looks_like_nav_query(request.query):
        scheme_hint = request.scheme or request.query
        
        # Check if fund is in our corpus before using AMFI lookup
        query_lower = request.query.lower()
        available_funds = [
            'hdfc_large_cap', 'hdfc_largecap',
            'hdfc_mid_cap', 'hdfc_midcap',
            'hdfc_equity',
            'hdfc_focused',
            'hdfc_elss', 'hdfc_tax_saver'
        ]
        
        mentioned_fund = None
        for fund in available_funds:
            if fund.replace('_', ' ') in query_lower or fund in query_lower:
                mentioned_fund = fund
                break
        
        # If query mentions a fund we don't have, return don't know
        if mentioned_fund is None and any(word in query_lower for word in ['hdfc', 'fund', 'scheme']):
            non_available_patterns = [
                'flexi cap', 'flexicap', 'small cap', 'smallcap',
                'balanced', 'hybrid', 'debt', 'liquid', 'gold',
                'nifty', 'index', 'etf', 'ppfas', 'parag',
                'quant', 'axis', 'icici', 'sbi', 'kotak', 'nippon'
            ]
            if any(pattern in query_lower for pattern in non_available_patterns):
                response = QueryResponse(
                    answer="I don't have information about that specific mutual fund scheme in my knowledge base. I can only answer for HDFC Large Cap, Mid Cap, Equity, Focused, and ELSS Tax Saver funds.",
                    source="",
                    scheme=request.scheme,
                    confidence=0.0,
                    route="fund_not_in_corpus",
                    include_url=False,
                )
                if cache:
                    cache.set(cache_key, response.dict(), ttl=3600)
                return response
        
        best, score = nav_client.find_best_match(scheme_hint)

        if best and score >= 0.55:
            answer = f"Latest NAV for {best.scheme_name} is {best.nav} (as of {best.nav_date})."
            response = QueryResponse(
                answer=answer,
                source=_groww_url_for_scheme(best.scheme_name),
                scheme=best.scheme_name,
                confidence=1.0,
                route="nav_lookup",
                include_url=True,
            )
        else:
            response = QueryResponse(
                answer="I couldn't match that scheme confidently for NAV. Please specify the exact variant (Direct/Regular + Growth/IDCWs).",
                source="",
                scheme=request.scheme,
                confidence=0.0,
                route="nav_not_found",
                include_url=False,
            )

        if cache:
            cache.set(cache_key, response.dict(), ttl=300)  # NAV changes; short cache
        return response

    # Expense ratio queries: extract from local raw HTML (Groww embedded JSON)
    if _looks_like_expense_ratio_query(request.query):
        scheme_hint = request.scheme or request.query

        # Try to detect multiple schemes mentioned in the query (e.g. "fund A and fund B")
        query_parts = re.split(r"\s+and\s+|\s+&\s+|\s+vs\.?\s+|\s+versus\s+", request.query.lower())
        candidates = [p.strip() for p in query_parts if p.strip()]
        if len(candidates) > 1:
            results = []
            seen_schemes = set()
            for part in candidates:
                found = expense_ratio_client.get_expense_ratio(part)
                if found and found.matched_scheme not in seen_schemes:
                    seen_schemes.add(found.matched_scheme)
                    results.append(found)
        else:
            found = expense_ratio_client.get_expense_ratio(scheme_hint)
            results = [found] if found else []

        if results:
            if len(results) == 1:
                answer = f"Latest expense ratio for {results[0].matched_scheme} is {results[0].expense_ratio}% (as of {results[0].as_on_date})."
            else:
                parts = [f"{r.matched_scheme}: {r.expense_ratio}% (as of {r.as_on_date})" for r in results]
                answer = "Latest expense ratios — " + "; ".join(parts) + "."
            source = _groww_url_for_query(request.query, request.scheme) if len(results) == 1 else "https://groww.in/mutual-funds"
            response = QueryResponse(
                answer=answer,
                source=source,
                scheme=request.scheme,
                confidence=1.0,
                route="expense_ratio_lookup",
                include_url=True,
            )
        else:
            response = QueryResponse(
                answer="I couldn't find an expense ratio value in the local scraped sources for that scheme.",
                source="",
                scheme=request.scheme,
                confidence=0.0,
                route="expense_ratio_not_found",
                include_url=False,
            )

        if cache:
            cache.set(cache_key, response.dict(), ttl=3600)
        return response

    # Other scheme facts (exit load, min SIP, benchmark, risk, lock-in, AUM)
    if _looks_like_scheme_facts_query(request.query):
        scheme_hint = request.scheme or request.query
        facts = scheme_facts_client.get_facts(scheme_hint)
        if not facts:
            response = QueryResponse(
                answer="I couldn't find that scheme in the local scraped sources.",
                source="",
                scheme=request.scheme,
                confidence=0.0,
                route="scheme_facts_not_found",
                include_url=False,
            )
        else:
            q = (request.query or "").lower()
            answer = None
            confidence = 0.0
            if "benchmark" in q:
                answer, confidence = _fact_answer("Benchmark index", facts.matched_scheme, facts.benchmark_index)
            elif "exit load" in q:
                answer, confidence = _fact_answer("Exit load", facts.matched_scheme, facts.exit_load)
            elif "sip" in q:
                answer, confidence = _fact_answer("Minimum SIP amount", facts.matched_scheme, facts.min_sip)
            elif "lumpsum" in q:
                answer, confidence = _fact_answer("Minimum lumpsum amount", facts.matched_scheme, facts.min_lumpsum)
            elif "lock" in q:
                answer, confidence = _fact_answer("Lock-in period", facts.matched_scheme, facts.lock_in)
            elif "risk" in q or "riskometer" in q:
                answer, confidence = _fact_answer("Risk classification", facts.matched_scheme, facts.risk_label)
            elif "aum" in q or "asset under management" in q or "assets under management" in q:
                answer, confidence = _fact_answer("AUM", facts.matched_scheme, facts.aum)
            elif any(kw in q for kw in ["fund manager", "who manages", "managed by", "manager of", "manager"]):
                answer, confidence = _fact_answer("Fund manager", facts.matched_scheme, facts.fund_manager)

            answer = answer or "I couldn't extract that specific field for this scheme from the local sources."
            source = _groww_url_for_query(request.query, request.scheme)
            response = QueryResponse(
                answer=answer,
                source=source,
                scheme=request.scheme,
                confidence=confidence,
                route="scheme_facts_lookup",
                include_url=True,
            )

        if cache:
            cache.set(cache_key, response.dict(), ttl=3600)
        return response
    
    # RAG / orchestrator fallback
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="RAG engine not available. Please try factual queries like expense ratio, NAV, exit load, or SIP.")
    
    try:
        result = orchestrator.process_query(request.query, scheme=request.scheme)

        # Parse source from formatted response text
        raw_source = result['response'].split('Source: ')[-1].split('\n')[0] if 'Source:' in result['response'] else ""
        # If source is missing or not a proper Groww URL, derive it from the query
        if not raw_source.startswith("https://groww.in"):
            raw_source = _groww_url_for_query(request.query, request.scheme)

        response = QueryResponse(
            answer=result['response'].split('\n')[0],  # First line is the answer
            source=raw_source,
            scheme=request.scheme,
            confidence=result.get('confidence', 0.0),
            route=result['route'],
            include_url=result['include_url']
        )
        
        # Cache the response
        if cache:
            cache.set(cache_key, response.dict(), ttl=3600)  # 1 hour TTL
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/api/schemes", response_model=SchemesResponse)
async def list_schemes():
    """
    List available mutual fund schemes.
    
    Returns:
        SchemesResponse with list of schemes
    """
    # For now, return schemes from the chunked data
    schemes = []
    try:
        import json
        import glob
        
        chunked_files = glob.glob('phase_2/scraped-data/chunked_json/*_chunked.json')
        for file_path in chunked_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                scheme_name = data.get('metadata', {}).get('scheme', os.path.basename(file_path).replace('_chunked.json', ''))
                schemes.append(SchemeInfo(
                    name=scheme_name,
                    category=data.get('metadata', {}).get('category'),
                    source_file=file_path
                ))
    except Exception as e:
        print(f"Error loading schemes: {e}")
    
    return SchemesResponse(schemes=schemes)


@app.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback on responses.
    
    Args:
        request: FeedbackRequest with query, answer, rating, and optional comment
        
    Returns:
        FeedbackResponse with status
    """
    # For now, just log the feedback
    print(f"Feedback received - Query: {request.query}, Rating: {request.rating}")
    if request.comment:
        print(f"Comment: {request.comment}")
    
    # In production, this would save to a database
    return FeedbackResponse(
        status="success",
        message="Feedback received successfully"
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
