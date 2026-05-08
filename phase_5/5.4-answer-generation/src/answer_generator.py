"""
Answer Generator Module
Generates answers from retrieved chunks (Groq primary, extractive fallback).
"""

import re
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


# Groww URL mapping — single source of truth
_GROWW_URLS = {
    "large_cap":  "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "mid_cap":    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "focused":    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "elss":       "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "equity":     "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
}

def _resolve_groww_url(text: str) -> str:
    """Resolve the correct Groww URL from any text containing fund identifiers."""
    t = text.lower()
    if "large_cap" in t or "large cap" in t or "largecap" in t:
        return _GROWW_URLS["large_cap"]
    if "mid_cap" in t or "mid cap" in t or "midcap" in t:
        return _GROWW_URLS["mid_cap"]
    if "focused" in t:
        return _GROWW_URLS["focused"]
    if "elss" in t or "tax_saver" in t or "tax saver" in t:
        return _GROWW_URLS["elss"]
    if "equity" in t or "flexi_cap" in t or "flexi cap" in t:
        return _GROWW_URLS["equity"]
    return "https://groww.in/mutual-funds"


class AnswerGenerator:
    """Generates answers from retrieved chunks using Groq LLM (primary) or extractive fallback."""

    def __init__(self, max_sentences: int = 3):
        self.max_sentences = max_sentences
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.use_groq = bool(self.groq_api_key)

        if self.use_groq:
            try:
                from openai import OpenAI
                self.groq_client = OpenAI(
                    api_key=self.groq_api_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                self.model = "llama-3.1-8b-instant"
                print(f"AnswerGenerator: Groq enabled ({self.model})")
            except ImportError:
                print("Warning: openai package not installed. Falling back to extractive mode.")
                self.use_groq = False

    # ------------------------------------------------------------------
    # Groq LLM path
    # ------------------------------------------------------------------

    def _clean_chunk_text(self, text: str) -> str:
        """Clean common scraping artefacts from chunk text before sending to LLM."""
        # Remove garbled 2-3 letter initials prefix on names: "DMDhruv" → "Dhruv", "AKAmar" → "Amar"
        text = re.sub(r'\b[A-Z]{2,3}([A-Z][a-z])', r'\1', text)
        # Remove "View details" noise
        text = re.sub(r'View\s+details', '', text, flags=re.IGNORECASE)
        # Collapse excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        return text.strip()

    def groq_answer(self, chunks: List[Dict[str, Any]], query: str) -> Optional[str]:
        """
        Generate answer using Groq LLM with ALL retrieved chunks as context.

        Args:
            chunks: List of retrieved chunks (top-k)
            query:  User query

        Returns:
            Answer string (≤ 3 sentences, no URLs) or None on failure.
        """
        if not self.use_groq or not chunks:
            return None

        # Build combined context from all chunks, labelled by source
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = self._clean_chunk_text(chunk.get('text', '').strip())
            scheme = chunk.get('metadata', {}).get('scheme_name', '')
            if text:
                label = f"[Chunk {i} – {scheme}]" if scheme else f"[Chunk {i}]"
                context_parts.append(f"{label}\n{text}")

        context = "\n\n".join(context_parts)

        system_prompt = (
            "You are a factual assistant for HDFC mutual fund queries. "
            "Answer ONLY using the provided context. "
            "Do NOT give investment advice, recommendations, or predictions. "
            "If the answer is not in the context, say: "
            "'I don't have enough information in my sources to answer that.' "
            "Keep your answer concise — at most 4 sentences or a short bullet list. "
            "If you see garbled text like 'DMDhruv Muchhal' or 'AGAmit Ganatra', "
            "interpret the real name by removing the leading 2-3 uppercase initials "
            "(e.g. 'DMDhruv Muchhal' → 'Dhruv Muchhal'). "
            "Do NOT include any URLs in your answer."
        )

        user_prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer (max 3 sentences, facts only, no URLs):"
        )

        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.1,   # very low — we want deterministic factual output
                max_tokens=250,
            )
            answer = response.choices[0].message.content.strip()
            # Strip any URLs the LLM may have hallucinated
            answer = re.sub(r'https?://\S+', '', answer).strip()
            return answer if answer else None

        except Exception as e:
            print(f"Groq API error: {e}")
            return None

    # ------------------------------------------------------------------
    # Extractive fallback
    # ------------------------------------------------------------------

    def extractive_answer(self, chunks: List[Dict[str, Any]], query: str = "") -> str:
        """
        Query-aware extractive answer from retrieved chunks (fallback when Groq unavailable).
        Scores every sentence across all chunks by keyword overlap with the query.
        """
        query_lower = (query or "").lower()

        stop_words = {
            'what', 'is', 'the', 'of', 'a', 'an', 'in', 'for', 'and', 'or',
            'to', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'who', 'how', 'when', 'where', 'which',
            'this', 'that', 'these', 'those', 'me', 'my', 'tell', 'about',
            'give', 'show', 'hdfc', 'fund',
        }
        query_keywords = {
            w for w in re.findall(r'\b[a-z]+\b', query_lower)
            if w not in stop_words
        }

        # Collect all sentences from all chunks
        all_sentences = []
        for chunk in chunks:
            text = chunk.get('text', '')
            sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
            for s in sentences:
                s = s.strip()
                if len(s) > 20:
                    all_sentences.append(s)

        if not all_sentences:
            return "I don't have enough information in my sources to answer that."

        if query_keywords:
            def score(s: str) -> int:
                sl = s.lower()
                return sum(1 for kw in query_keywords if kw in sl)

            scored = sorted(enumerate(all_sentences), key=lambda x: score(x[1]), reverse=True)
            top_indices = sorted([i for i, _ in scored[:self.max_sentences]])
            answer_sentences = [all_sentences[i] for i in top_indices]
        else:
            answer_sentences = all_sentences[:self.max_sentences]

        answer = ' '.join(answer_sentences)
        answer = re.sub(r'https?://\S+', '', answer)
        return answer.strip()

    # ------------------------------------------------------------------
    # Source URL resolution
    # ------------------------------------------------------------------

    def get_source_url(self, chunks: List[Dict[str, Any]], query: str = "") -> str:
        """Resolve the correct Groww URL from chunk metadata + query."""
        # Try each chunk's metadata
        for chunk in chunks:
            meta = chunk.get('metadata', {})
            combined = f"{meta.get('scheme_name', '')} {meta.get('source_file', '')}".lower()
            url = _resolve_groww_url(combined)
            if url != "https://groww.in/mutual-funds":
                return url
        # Fall back to query text
        return _resolve_groww_url(query)

    # ------------------------------------------------------------------
    # Format
    # ------------------------------------------------------------------

    def format_response(self, answer: str, source_url: str, include_url: bool = True) -> str:
        lines = [answer]
        if include_url and source_url:
            lines.append(f"Source: {source_url}")
        lines.append(f"Last updated from sources: {datetime.now().strftime('%Y-%m-%d')}")
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Main entry point — called by orchestrator
    # ------------------------------------------------------------------

    def generate(
        self,
        chunks: List[Dict[str, Any]],
        query: str = "",
        include_url: bool = True,
    ) -> str:
        """
        Generate a complete response.

        Args:
            chunks:      All retrieved chunks (top-k list).
            query:       User query.
            include_url: Whether to append the source URL.

        Returns:
            Formatted response string.
        """
        # Normalise: accept a single chunk dict for backward compatibility
        if isinstance(chunks, dict):
            chunks = [chunks]

        # Primary: Groq LLM with all chunks as context
        answer = None
        if self.use_groq and query:
            answer = self.groq_answer(chunks, query)

        # Fallback: extractive
        if not answer:
            answer = self.extractive_answer(chunks, query=query)

        source_url = self.get_source_url(chunks, query=query)
        return self.format_response(answer, source_url, include_url)
