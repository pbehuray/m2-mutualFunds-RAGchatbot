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
import sys
import json
import requests
from datetime import datetime
from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup — allow direct imports when FastAPI is not running
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE = os.environ.get(
    "API_BASE_URL",
    st.secrets.get("api_base_url", "http://localhost:8002"),
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
    page_title="HDFC MF Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
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
    """Send a query to the backend and return the response."""
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
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Groww_logo.png/600px-Groww_logo.png",
            width=120,
        )
        st.title("HDFC MF Assistant")
        st.caption("Facts-only. No investment advice.")

        st.divider()

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

        # Health status
        st.subheader("System Status")
        health = get_health()
        if health:
            status_emoji = "🟢" if health.get("orchestrator_ready") else "🟡"
            st.markdown(f"{status_emoji} **API**: {health.get('status', 'unknown')}")
            st.markdown(f"🔄 **Orchestrator**: {'Ready' if health.get('orchestrator_ready') else 'Not loaded'}")
            st.markdown(f"📦 **Version**: {health.get('version', 'N/A')}")
        else:
            st.markdown("🔴 **API**: Unreachable")
            st.caption(f"Expected at `{API_BASE}`")

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
    st.title("📈 HDFC Mutual Fund FAQ Assistant")
    st.caption("Ask factual questions about HDFC mutual fund schemes — expense ratio, NAV, exit load, SIP, lock-in, riskometer, and more.")

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
