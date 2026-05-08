"""
Scheme facts extractor (local Groww HTML).

This is a deterministic fallback for facts-only fields that are present in the
saved HTML but not reliably retrievable via embeddings.
"""

from __future__ import annotations

import html as html_lib
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional, Tuple


RAW_HTML_DIR = os.path.join("phase_2", "scraped-data", "raw_html")


def _normalize(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _normalize_html_text(raw: str) -> str:
    text = html_lib.unescape(raw or "")
    text = text.replace("â‚¹", "\u20b9").replace("\\u20b9", "\u20b9")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_inr_amount(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    raw = html_lib.unescape(raw).replace("â‚¹", "\u20b9").replace("?", "\u20b9")
    m = re.search(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(Cr|L|K|crore|lakh)?", raw, flags=re.IGNORECASE)
    if not m:
        return None
    suffix = f" {m.group(2)}" if m.group(2) else ""
    return f"\u20b9{m.group(1)}{suffix}"


@dataclass(frozen=True)
class SchemeFacts:
    matched_scheme: str
    benchmark_index: Optional[str]
    risk_label: Optional[str]
    min_sip: Optional[str]
    min_lumpsum: Optional[str]
    exit_load: Optional[str]
    lock_in: Optional[str]
    aum: Optional[str]
    fund_manager: Optional[str]
    source_url: str


class SchemeFactsClient:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root

    def _raw_dir_abs(self) -> str:
        return os.path.join(self.workspace_root, RAW_HTML_DIR)

    def _list_html_files(self) -> List[str]:
        base = self._raw_dir_abs()
        if not os.path.isdir(base):
            return []
        return [
            os.path.join(base, f)
            for f in os.listdir(base)
            if f.lower().endswith(".html")
        ]

    def _best_file_match(self, scheme_query: str) -> Tuple[Optional[str], float]:
        q = _normalize(scheme_query)
        if not q:
            return None, 0.0

        # Build a set of all tokens that appear in any filename so we can
        # drop query words that are clearly fact-query keywords (e.g. lock,
        # exit, load, sip, lumpsum, benchmark, risk, aum, manager).
        all_cand_tokens: set = set()
        files = self._list_html_files()
        for path in files:
            fname = os.path.basename(path)
            cand = _normalize(fname.replace(".html", ""))
            all_cand_tokens.update(cand.split())

        q_tokens = set(q.split())
        # Keep only query tokens that appear in at least one filename
        relevant_tokens = q_tokens & all_cand_tokens
        q_filtered = " ".join(sorted(relevant_tokens)) if relevant_tokens else q
        qf_tokens = set(q_filtered.split())

        best_path = None
        best_score = 0.0
        for path in files:
            fname = os.path.basename(path)
            cand = _normalize(fname.replace(".html", ""))
            cand_tokens = set(cand.split())
            intersection = qf_tokens & cand_tokens

            sequence_score = SequenceMatcher(None, q_filtered, cand).ratio()
            # Token score: if all query tokens are present, boost heavily
            if qf_tokens and qf_tokens.issubset(cand_tokens):
                token_score = 0.85
            else:
                token_score = len(intersection) / max(len(cand_tokens), 1)

            score = max(sequence_score, token_score)
            if score > best_score:
                best_score = score
                best_path = path
        return best_path, best_score

    def _extract_source_url(self, html_text: str) -> str:
        # Always prefer the canonical URL — it's the most reliable and user-friendly
        m = re.search(r'rel="canonical"[^>]+href="([^"]+)"', html_text, re.IGNORECASE)
        if not m:
            m = re.search(r'href="([^"]+)"[^>]+rel="canonical"', html_text, re.IGNORECASE)
        if m:
            return m.group(1)

        # Fallback: Scheme Information Document link
        m = re.search(
            r'<a[^>]+href="([^"]+)"[^>]*>\s*<span>\s*Scheme Information Document\(SID\)\s*</span>',
            html_text,
            flags=re.IGNORECASE,
        )
        if m:
            return m.group(1)

        return ""

    def _extract_benchmark(self, html_text: str) -> Optional[str]:
        m = re.search(
            r"Fund benchmark</span><span[^>]*>([^<]+)</span>",
            html_text,
            flags=re.IGNORECASE,
        )
        return html_lib.unescape(m.group(1)).strip() if m else None

    def _extract_summary_fields(self, html_text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        risk = None
        min_sip = None
        exit_load = None

        meta_desc = None
        md = re.search(
            r'<meta[^>]+name="description"[^>]+content="([^"]+)"',
            html_text,
            flags=re.IGNORECASE,
        )
        if md:
            meta_desc = html_lib.unescape(md.group(1))

        if meta_desc and any(t in meta_desc.lower() for t in ("minimum sip", "exit load", "rated ")):
            hay = _normalize_html_text(meta_desc)
        else:
            hay = _normalize_html_text(html_text)

        m = re.search(r"rated\s+([^.]+?)\s+risk\.", hay, flags=re.IGNORECASE)
        if m:
            risk = m.group(1).strip() + " risk"

        m = re.search(r"Minimum SIP Investment is set to\s*(?:Rs\.?\s*)?([\u20b9?]?\s*[0-9,]+)", hay, flags=re.IGNORECASE)
        if m:
            min_sip = _clean_inr_amount(m.group(1))

        m = re.search(
            r"Exit load of\s*(.*?)(?:\s+\d{2}\s+[A-Z][a-z]{2}\s+\d{4}|\s+Exit load,|;|\.|$)",
            hay,
            flags=re.IGNORECASE,
        )
        if m:
            exit_load = m.group(1).strip()

        return risk, min_sip, exit_load

    def _extract_min_lumpsum(self, html_text: str) -> Optional[str]:
        hay = _normalize_html_text(html_text)
        m = re.search(r"Minimum Lumpsum Investment is\s*(?:Rs\.?\s*)?([\u20b9?]?\s*[0-9,]+)", hay, flags=re.IGNORECASE)
        if m:
            return _clean_inr_amount(m.group(1))
        return None

    def _extract_lock_in(self, html_text: str) -> Optional[str]:
        # Pattern 1: JSON analysis blob — "analysis_subject":"lock_in","analysis_desc":"Lock-in period: 3Y"
        m = re.search(
            r'"analysis_subject"\s*:\s*"lock_in"[^}]*"analysis_desc"\s*:\s*"([^"]+)"',
            html_text, re.IGNORECASE
        )
        if m:
            return html_lib.unescape(m.group(1)).strip()

        # Pattern 2: pill label — "ELSS • 3Y Lock-in" or "3Y Lock-in"
        m = re.search(r'(\d+\s*(?:Y|year|years?))\s*Lock-?in', html_text, re.IGNORECASE)
        if m:
            years = m.group(1).strip()
            return f"{years} lock-in period"

        # Pattern 3: JSON field "lock_in" with numeric value
        m = re.search(r'"lock_in"\s*:\s*"?(\d+)"?', html_text, re.IGNORECASE)
        if m:
            return f"{m.group(1)} year lock-in period"

        # Pattern 4: plain text fallback
        hay = _normalize_html_text(html_text)
        m = re.search(r"lock[- ]in\s+(?:period\s+(?:of\s+)?)?([^.]{2,40})\.", hay, re.IGNORECASE)
        if m:
            return m.group(1).strip()

        return None

    def _extract_aum(self, html_text: str) -> Optional[str]:
        # Prefer scheme-level AUM. Fund-house "Total AUM" / meta-description AUM is a different (larger) number.
        # Check the "Fund size (AUM)" widget first \u2014 it shows scheme AUM.
        html_patterns = [
            r"Fund size \(AUM\)</div><div[^>]*>([^<]+)</div>",
            r"Fund size</span><span[^>]*>([^<]+)</span>",
        ]
        for pattern in html_patterns:
            m = re.search(pattern, html_text, flags=re.IGNORECASE)
            if m:
                val = _clean_inr_amount(m.group(1))
                if val:
                    return val

        # Fallback: text-level patterns (may match fund-house AUM if scheme widget absent)
        text = _normalize_html_text(html_text)
        text_patterns = [
            r"\bAUM\b[^.]{0,180}?\bis\s*([\u20b9?]\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:Cr|crore|L|lakh)?)\s+as of",
            r"Asset Under Management\s*\(AUM\)\s+of\s*([\u20b9?]\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*(?:Cr|crore|L|lakh)?)",
        ]
        for pattern in text_patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                return _clean_inr_amount(m.group(1))

        return None

    def _extract_fund_manager(self, html_text: str) -> Optional[str]:
        """Extract fund manager name from Groww HTML."""
        # Pattern 1: JSON-LD or data attributes with manager name
        m = re.search(r'"fundManager"\s*:\s*"([^"]+)"', html_text, re.IGNORECASE)
        if m:
            return html_lib.unescape(m.group(1)).strip()

        # Pattern 2: Groww HTML structure — initials div followed by name div
        # <div class="...fundManagement_initials...">CS</div><div ...>Chirag Setalvad</div>
        m = re.search(
            r'fundManagement_initials[^>]+>[A-Z]{2,3}</div>.*?<div[^>]*>([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})</div>',
            html_text, re.DOTALL
        )
        if m:
            return html_lib.unescape(m.group(1)).strip()

        # Pattern 3: meta description — "managed by <Name>"
        text = re.sub(r'<[^>]+>', ' ', html_text)
        text = re.sub(r'\s+', ' ', html_lib.unescape(text))
        m = re.search(r'managed by ([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()

        return None

    def get_facts(self, scheme_query: str) -> Optional[SchemeFacts]:
        file_path, score = self._best_file_match(scheme_query)
        if not file_path or score < 0.45:
            return None

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                html_text = f.read()
        except Exception:
            return None

        matched_scheme = os.path.basename(file_path).replace(".html", "").replace("_", " ")

        risk, min_sip, exit_load = self._extract_summary_fields(html_text)
        benchmark = self._extract_benchmark(html_text)
        min_lumpsum = self._extract_min_lumpsum(html_text)
        lock_in = self._extract_lock_in(html_text)
        # ELSS funds have a mandatory 3-year lock-in by law (Section 80C)
        if not lock_in and ("elss" in matched_scheme.lower() or "tax_saver" in matched_scheme.lower()):
            lock_in = "3 years"
        aum = self._extract_aum(html_text)
        fund_manager = self._extract_fund_manager(html_text)
        source_url = self._extract_source_url(html_text) or file_path
        return SchemeFacts(
            matched_scheme=matched_scheme,
            benchmark_index=benchmark,
            risk_label=risk,
            min_sip=min_sip,
            min_lumpsum=min_lumpsum,
            exit_load=exit_load,
            lock_in=lock_in,
            aum=aum,
            fund_manager=fund_manager,
            source_url=source_url,
        )
