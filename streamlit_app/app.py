"""
Phase 11: Streamlit Deployment — Mutual Fund FAQ Assistant
==========================================================
A Streamlit web application that connects to the FastAPI backend
or falls back to direct Python module imports.

Run locally:
    streamlit run app.py

Deploy to Streamlit Community Cloud:
    Push to GitHub → share.streamlit.io → New app
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Configuration - Option A: External FastAPI Backend on Render
# ---------------------------------------------------------------------------
API_BASE = os.environ.get(
    "API_BASE_URL",
    st.secrets.get("api_base_url", "https://mf-chatbot-api.onrender.com"),
)
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", 30))

SUPPORTED_SCHEMES = [
    "HDFC Large Cap Fund Direct Growth",
    "HDFC Mid Cap Fund Direct Growth",
    "HDFC Equity Fund Direct Growth",
    "HDFC Focused Fund Direct Growth",
    "HDFC ELSS Tax Saver Fund Direct Plan Growth",
]

SUGGESTED_QUERIES = [
    "What is the expense ratio of HDFC Focused Fund?",
    "Min SIP for HDFC Mid Cap Fund?",
    "Exit load of HDFC Equity Fund?",
    "NAV of HDFC Large Cap Fund?",
    "Lock-in period for HDFC ELSS Tax Saver?",
    "Risk level of HDFC Focused Fund?",
    "Benchmark of HDFC Mid Cap Fund?",
    "Expense ratio of HDFC Focused Fund and HDFC Mid Cap Fund?",
]

# ---------------------------------------------------------------------------
# Page configuration (11.1)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GROWW RAG",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --groww-green: #00d09c;
        --groww-green-dark: #00a77d;
        --bg-main: #050b0a;
        --bg-panel: #0b1412;
        --bg-card: #101c19;
        --text-main: #f4fffb;
        --text-muted: #a8b8b2;
        --border-soft: rgba(0, 208, 156, 0.18);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(0, 208, 156, 0.16), transparent 34rem),
            linear-gradient(135deg, #050b0a 0%, #07110f 45%, #020403 100%);
        color: var(--text-main);
    }

    header[data-testid="stHeader"] {
        background: #050b0a;
        border-bottom: 1px solid var(--border-soft);
    }

    [data-testid="stToolbar"] {
        background: #050b0a;
    }

    [data-testid="stDecoration"] {
        background: var(--groww-green);
    }

    .block-container {
        background: transparent;
    }

    section.main > div {
        background: transparent;
    }

    [data-testid="stBottomBlockContainer"] {
        background: #050b0a;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #07110f 0%, #050b0a 100%);
        border-right: 1px solid var(--border-soft);
    }

    [data-testid="stSidebar"] * {
        color: var(--text-main);
    }

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] small,
    .stCaption,
    div[data-testid="stMarkdownContainer"] p {
        color: var(--text-muted);
    }

    h1, h2, h3 {
        color: var(--text-main);
        letter-spacing: -0.03em;
    }

    .groww-hero {
        padding: 2rem;
        border: 1px solid var(--border-soft);
        border-radius: 1.5rem;
        background:
            linear-gradient(135deg, rgba(0, 208, 156, 0.16), rgba(0, 208, 156, 0.03)),
            rgba(11, 20, 18, 0.92);
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
        margin-bottom: 1.4rem;
    }

    .groww-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.38rem 0.75rem;
        border: 1px solid var(--border-soft);
        border-radius: 999px;
        color: var(--groww-green);
        background: rgba(0, 208, 156, 0.08);
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 0.9rem;
    }

    .groww-hero h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.4rem);
        line-height: 1.05;
    }

    .groww-hero p {
        margin-top: 0.85rem;
        max-width: 760px;
        color: var(--text-muted);
        font-size: 1.05rem;
    }

    div[data-testid="stExpander"],
    div[data-testid="stForm"],
    [data-testid="stChatMessage"] {
        border: 1px solid var(--border-soft);
        border-radius: 1rem;
        background: rgba(16, 28, 25, 0.78);
    }

    [data-testid="stChatMessage"] {
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
    }

    .stButton > button {
        border: 1px solid rgba(0, 208, 156, 0.28);
        border-radius: 999px;
        background: rgba(0, 208, 156, 0.10);
        color: var(--text-main);
        transition: all 0.18s ease;
    }

    .stButton > button:hover {
        border-color: var(--groww-green);
        background: var(--groww-green);
        color: #02110d;
        transform: translateY(-1px);
    }

    .stSelectbox div[data-baseweb="select"] > div,
    .stTextInput input,
    textarea {
        background-color: #0b1412;
        border-color: var(--border-soft);
        color: var(--text-main);
    }

    [data-testid="stChatInput"] {
        background: rgba(5, 11, 10, 0.92);
        border-top: 1px solid var(--border-soft);
    }

    [data-testid="stChatInput"] > div {
        background: #050b0a;
    }

    [data-testid="stChatInput"] textarea {
        background: #0b1412;
        color: var(--text-main);
        border: 1px solid var(--border-soft);
    }

    hr {
        border-color: var(--border-soft);
    }

    a {
        color: var(--groww-green) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialization (11.1)
# ---------------------------------------------------------------------------
def init_session_state():
    defaults = {
        "messages": [],
        "feedback_given": set(),
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

init_session_state()

# ---------------------------------------------------------------------------
# API client helpers (11.4)
# ---------------------------------------------------------------------------
def _api_get(endpoint: str, params: dict = None) -> Optional[dict]:
    """GET request to the FastAPI backend."""
    try:
        resp = requests.get(
            f"{API_BASE}{endpoint}",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return None
    except requests.Timeout:
        return None
    except requests.HTTPError:
        return None


def _api_post(endpoint: str, payload: dict) -> Optional[dict]:
    """POST request to the FastAPI backend."""
    try:
        resp = requests.post(
            f"{API_BASE}{endpoint}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return None
    except requests.Timeout:
        return None
    except requests.HTTPError as e:
        try:
            return resp.json()
        except Exception:
            return {"error": str(e)}


def query_backend(query: str, scheme: str = None) -> dict:
    """Send query to FastAPI backend via HTTP."""
    payload = {"query": query}
    if scheme:
        payload["scheme"] = scheme
    result = _api_post("/api/query", payload)
    if result is None:
        return {
            "answer": "Backend is unavailable. Please make sure the FastAPI server is running.",
            "source": "",
            "scheme": None,
            "confidence": 0.0,
            "route": "error",
            "include_url": False,
        }
    return result


def get_health() -> Optional[dict]:
    return _api_get("/api/health")


def get_schemes() -> Optional[dict]:
    return _api_get("/api/schemes")


def submit_feedback(query: str, answer: str, rating: str, comment: str = None):
    payload = {"query": query, "answer": answer, "rating": rating}
    if comment:
        payload["comment"] = comment
    return _api_post("/api/feedback", payload)


# ---------------------------------------------------------------------------
# Sidebar (11.2 + 11.3)
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        # Scheme selector
        st.subheader("Scheme Selector")
        selected_scheme = st.selectbox(
            "Pre-select a scheme",
            options=["(auto-detect)"] + SUPPORTED_SCHEMES,
            index=0,
            label_visibility="collapsed",
        )
        scheme_value = None if selected_scheme == "(auto-detect)" else selected_scheme

        st.divider()

        # Supported schemes list
        st.subheader("Supported Schemes")
        for scheme in SUPPORTED_SCHEMES:
            st.markdown(f"- {scheme}")

        st.divider()

        # Session controls
        st.subheader("Session")
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.feedback_given = set()
            st.rerun()

        st.caption(f"Messages: {len(st.session_state.messages)}")

    return scheme_value


# ---------------------------------------------------------------------------
# Dashboard (11.3)
# ---------------------------------------------------------------------------
def render_dashboard():
    """Render fund fact cards at the top of the main area."""
    st.subheader("📊 Fund Overview")

    schemes_data = get_schemes()
    scheme_names = []
    if schemes_data and "schemes" in schemes_data:
        scheme_names = [s["name"] for s in schemes_data["schemes"]]

    if not scheme_names:
        scheme_names = SUPPORTED_SCHEMES

    cols = st.columns(min(len(scheme_names), 5))
    for i, scheme in enumerate(scheme_names[:5]):
        with cols[i]:
            # Fetch quick facts
            facts = query_backend(f"scheme facts for {scheme}")
            answer = facts.get("answer", "No data available")

            # Parse key facts from answer for display
            display_name = scheme.replace("HDFC ", "").replace(" Direct Growth", "").replace(" Direct Plan Growth", "")
            st.markdown(f"**{display_name}**")

            # Show abbreviated answer
            if "couldn't" not in answer.lower() and "no data" not in answer.lower():
                # Show first 150 chars
                short = answer[:150] + ("..." if len(answer) > 150 else "")
                st.caption(short)
            else:
                st.caption("Click to query →")

            if st.button("Ask", key=f"ask_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": f"Tell me about {scheme}"})
                with st.spinner("Thinking..."):
                    response = query_backend(f"Tell me about {scheme}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.get("answer", "No response"),
                    "source": response.get("source", ""),
                    "confidence": response.get("confidence", 0.0),
                    "route": response.get("route", ""),
                    "query": f"Tell me about {scheme}",
                })
                st.rerun()

    st.divider()


# ---------------------------------------------------------------------------
# Chat interface (11.2)
# ---------------------------------------------------------------------------
def render_chat(scheme_value: Optional[str]):
    """Render the main chat interface."""

    # Display existing messages
    for i, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        content = msg["content"]

        with st.chat_message(role):
            st.markdown(content)

            # Show source link and feedback for assistant messages
            if role == "assistant" and i not in st.session_state.feedback_given:
                source = msg.get("source", "")
                confidence = msg.get("confidence", 0.0)
                route = msg.get("route", "")
                query = msg.get("query", "")

                # Source link
                if source and msg.get("include_url", True):
                    st.markdown(f"🔗 [Source]({source})")

                # Confidence badge
                conf_emoji = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.5 else "🔴"
                st.caption(f"{conf_emoji} Confidence: {confidence:.0%} | Route: {route}")

                # Feedback buttons
                fb_col1, fb_col2 = st.columns(2)
                with fb_col1:
                    if st.button("👍 Helpful", key=f"up_{i}", use_container_width=True):
                        submit_feedback(query, content, "thumbs_up")
                        st.session_state.feedback_given.add(i)
                        st.toast("Thanks for your feedback!")
                        st.rerun()
                with fb_col2:
                    if st.button("👎 Not helpful", key=f"down_{i}", use_container_width=True):
                        submit_feedback(query, content, "thumbs_down")
                        st.session_state.feedback_given.add(i)
                        st.toast("We'll improve. Thanks!")
                        st.rerun()

    # Suggested queries
    st.markdown("**Try asking:**")
    chip_cols = st.columns(4)
    for j, suggestion in enumerate(SUGGESTED_QUERIES[:8]):
        with chip_cols[j % 4]:
            if st.button(suggestion, key=f"suggest_{j}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": suggestion})
                with st.spinner("Thinking..."):
                    response = query_backend(suggestion, scheme=scheme_value)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.get("answer", "No response"),
                    "source": response.get("source", ""),
                    "confidence": response.get("confidence", 0.0),
                    "route": response.get("route", ""),
                    "include_url": response.get("include_url", True),
                    "query": suggestion,
                })
                st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask about HDFC mutual funds..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Thinking..."):
            response = query_backend(prompt, scheme=scheme_value)
        st.session_state.messages.append({
            "role": "assistant",
            "content": response.get("answer", "No response"),
            "source": response.get("source", ""),
            "confidence": response.get("confidence", 0.0),
            "route": response.get("route", ""),
            "include_url": response.get("include_url", True),
            "query": prompt,
        })
        st.rerun()


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    # Sidebar
    scheme_value = render_sidebar()

    # Main area header
    st.markdown(
        """
        <section class="groww-hero">
            <div class="groww-pill">● Mutual fund RAG · Facts-only assistant</div>
            <h1>GROWW RAG</h1>
            <p>
                Retrieves facts from curated mutual fund sources.<br>
                Answers questions on expense ratio, NAV, SIP, exit load, risk, and benchmark.<br>
                Shows source-backed responses without giving investment advice.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Dashboard (collapsible)
    with st.expander("📊 Fund Overview Dashboard", expanded=False):
        render_dashboard()

    # Chat
    render_chat(scheme_value)

    # Footer
    st.divider()
    st.caption("Facts-only. No investment advice. Sources: Groww / HDFC / AMFI / SEBI")


if __name__ == "__main__":
    main()
