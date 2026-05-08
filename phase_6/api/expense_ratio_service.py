"""
Expense ratio lookup service.

The scraped Groww pages in `phase_2/scraped-data/raw_html` often contain the
expense ratio in embedded JSON (e.g. `"expense_ratio":0.77,"as_on_date":"..."`),
but that value does not always appear in the cleaned chunk text used for RAG.

This module extracts the latest expense ratio for a requested scheme from the
local raw HTML files.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional, Tuple, List


RAW_HTML_DIR = os.path.join("phase_2", "scraped-data", "raw_html")


def _normalize(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _scheme_terms(s: str) -> str:
    words = _normalize(s).split()
    stop_words = {
        "what",
        "is",
        "the",
        "of",
        "for",
        "expense",
        "expence",
        "ratio",
        "ration",
        "ter",
    }
    return " ".join(word for word in words if word not in stop_words)


@dataclass(frozen=True)
class ExpenseRatioResult:
    matched_scheme: str
    expense_ratio: float
    as_on_date: str  # ISO string
    source_file: str


class ExpenseRatioClient:
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
        q = _scheme_terms(scheme_query)
        if not q:
            return None, 0.0

        best_path = None
        best_score = 0.0
        for path in self._list_html_files():
            fname = os.path.basename(path)
            # filenames are snake-ish; normalize helps
            cand = _normalize(fname.replace(".html", ""))
            sequence_score = SequenceMatcher(None, q, cand).ratio()
            q_tokens = set(q.split())
            cand_tokens = set(cand.split())
            token_score = len(q_tokens & cand_tokens) / max(len(q_tokens), 1)
            score = max(sequence_score, token_score)
            if score > best_score:
                best_score = score
                best_path = path
        return best_path, best_score

    def _extract_latest(self, html_text: str) -> Optional[Tuple[float, str]]:
        # Capture repeated pairs; some pages include many daily values.
        pattern = re.compile(
            r"\"expense_ratio\"\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*,\s*\"as_on_date\"\s*:\s*\"([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})\"",
            flags=re.IGNORECASE,
        )
        matches = pattern.findall(html_text)
        if not matches:
            return None

        best_ratio = None
        best_date = None
        for ratio_s, date_s in matches:
            try:
                ratio = float(ratio_s)
                dt = datetime.fromisoformat(date_s)
            except Exception:
                continue
            if best_date is None or dt > best_date:
                best_date = dt
                best_ratio = ratio

        if best_ratio is None or best_date is None:
            return None
        return best_ratio, best_date.isoformat()

    def _extract_preferred_source_url(self, html_text: str) -> str:
        # Prefer an AMC/SID link if present; else fall back to Groww canonical.
        m = re.search(
            r'<a[^>]+href="([^"]+)"[^>]*>\s*<span>\s*Scheme Information Document\\(SID\\)\s*</span>',
            html_text,
            flags=re.IGNORECASE,
        )
        if m:
            return m.group(1)

        m = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html_text, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        return ""

    def get_expense_ratio(self, scheme_query: str) -> Optional[ExpenseRatioResult]:
        file_path, score = self._best_file_match(scheme_query)
        if not file_path or score < 0.45:
            return None

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                html_text = f.read()
        except Exception:
            return None

        latest = self._extract_latest(html_text)
        if not latest:
            return None

        ratio, as_on_date = latest
        matched_scheme = os.path.basename(file_path).replace(".html", "").replace("_", " ")
        return ExpenseRatioResult(
            matched_scheme=matched_scheme,
            expense_ratio=ratio,
            as_on_date=as_on_date,
            source_file=self._extract_preferred_source_url(html_text) or file_path,
        )
