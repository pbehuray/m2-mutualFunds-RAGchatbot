"""
NAV lookup service (AMFI daily NAV feed).

This module intentionally uses only the Python standard library so it works with
the existing Phase 6 requirements.
"""

from __future__ import annotations

import re
import time
import urllib.request
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional, Tuple


AMFI_NAVALL_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# Known fund renames: maps user-facing aliases / old names → canonical AMFI name fragment.
# The value is matched as a substring (case-insensitive, normalised) against AMFI scheme names.
FUND_ALIASES: dict[str, str] = {
    # HDFC Equity Fund was renamed to HDFC Flexi Cap Fund
    "hdfc equity fund direct growth": "hdfc flexi cap fund growth option direct plan",
    "hdfc equity fund direct plan growth": "hdfc flexi cap fund growth option direct plan",
    "hdfc equity direct growth": "hdfc flexi cap fund growth option direct plan",
    "hdfc equity fund": "hdfc flexi cap fund direct",
    "hdfc equity": "hdfc flexi cap fund direct",
}


def _normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _apply_alias(query: str) -> str:
    """Replace known old/alias fund names with their current AMFI canonical name."""
    q = query.lower().strip()
    for alias, canonical in FUND_ALIASES.items():
        if alias in q:
            return canonical
    return query


@dataclass(frozen=True)
class NavRecord:
    scheme_code: str
    scheme_name: str
    nav: str
    nav_date: str


class AmfiNavClient:
    def __init__(self, ttl_seconds: int = 60 * 30, timeout_seconds: int = 15):
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds
        self._cached_at: float = 0.0
        self._cached_records: List[NavRecord] = []

    def _download_text(self) -> str:
        req = urllib.request.Request(
            AMFI_NAVALL_URL,
            headers={
                "User-Agent": "MutualFundFAQAssistant/1.0 (NAV lookup; educational use)"
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            raw = resp.read()
        # NAVAll.txt is typically UTF-8; fall back gracefully
        return raw.decode("utf-8", errors="replace")

    def _parse_records(self, text: str) -> List[NavRecord]:
        records: List[NavRecord] = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Data lines are semicolon-separated; header/section lines are not reliable.
            parts = [p.strip() for p in line.split(";")]
            if len(parts) < 6:
                continue

            scheme_code = parts[0]
            scheme_name = parts[3]
            nav = parts[4]
            nav_date = parts[5]

            # Basic validation
            if not scheme_code.isdigit():
                continue
            if not scheme_name or nav in ("", "N.A.", "NA"):
                continue

            records.append(
                NavRecord(
                    scheme_code=scheme_code,
                    scheme_name=scheme_name,
                    nav=nav,
                    nav_date=nav_date,
                )
            )
        return records

    def get_records(self, force_refresh: bool = False) -> List[NavRecord]:
        now = time.time()
        if (
            not force_refresh
            and self._cached_records
            and (now - self._cached_at) < self.ttl_seconds
        ):
            return self._cached_records

        text = self._download_text()
        records = self._parse_records(text)
        self._cached_records = records
        self._cached_at = now
        return records

    def find_best_match(self, scheme_query: str) -> Tuple[Optional[NavRecord], float]:
        # Resolve known renames/aliases before any fuzzy matching
        resolved_query = _apply_alias(scheme_query)
        q = _normalize(resolved_query)
        if not q:
            return None, 0.0

        q_tokens = set(q.split())
        # Keep only "signal" tokens (short tokens tend to over-match)
        q_tokens = {t for t in q_tokens if len(t) >= 3}

        # If the user mentions a fund house explicitly, require it.
        must_have_tokens = set()
        for brand in ("hdfc", "icici", "sbi", "axis", "kotak", "nippon", "uti", "aditya", "birla", "tata", "canara", "hsbc"):
            if brand in q_tokens:
                must_have_tokens.add(brand)

        # Tokens that are "distinguishing" — if present in query they MUST appear in the match.
        # These are fund-type words that clearly identify a specific fund category.
        distinguishing_tokens = {
            "equity", "largecap", "midcap", "flexi", "focused", "elss",
            "large", "mid", "small", "balanced", "hybrid", "debt", "liquid",
            "duration", "credit", "gilt", "arbitrage", "multi",
        }
        # Which distinguishing tokens does the query contain?
        q_distinguishing = q_tokens.intersection(distinguishing_tokens)

        best: Optional[NavRecord] = None
        best_score = 0.0
        for rec in self.get_records():
            name_norm = _normalize(rec.scheme_name)
            name_tokens = set(name_norm.split())

            if must_have_tokens and not must_have_tokens.issubset(name_tokens):
                continue

            # Require some token overlap to avoid accidental brand mismatches
            overlap = len(q_tokens.intersection(name_tokens)) if q_tokens else 0
            if q_tokens and overlap < min(2, len(q_tokens)):
                continue

            # Hard filter: every distinguishing token in the query must appear in the candidate.
            # This prevents "equity" query matching "low duration" or "mid cap" etc.
            if q_distinguishing and not q_distinguishing.issubset(name_tokens):
                continue

            score = SequenceMatcher(None, q, name_norm).ratio()
            # Reward token overlap
            score += min(0.15, overlap * 0.03)

            # Prefer exact phrase matches when present in query
            if "large cap" in q and "large cap" in name_norm:
                score += 0.08
            if "flexi cap" in q and "flexi cap" in name_norm:
                score += 0.08
            if "mid cap" in q and "mid cap" in name_norm:
                score += 0.08

            # Reward direct plan match when query asks for direct
            if "direct" in q_tokens and "direct" in name_tokens:
                score += 0.10
            elif "direct" in q_tokens and "direct" not in name_tokens:
                score -= 0.10

            # Reward growth match when query asks for growth
            if "growth" in q_tokens and "growth" in name_tokens:
                score += 0.05
            elif "growth" in q_tokens and "growth" not in name_tokens:
                score -= 0.05

            # Penalize extra descriptors in candidate that are NOT in the query
            if "mid" in name_tokens and "mid" not in q_tokens:
                score -= 0.10
            if "small" in name_tokens and "small" not in q_tokens:
                score -= 0.08
            if "hybrid" in name_tokens and "hybrid" not in q_tokens:
                score -= 0.10
            if "savings" in name_tokens and "savings" not in q_tokens:
                score -= 0.10
            if "duration" in name_tokens and "duration" not in q_tokens:
                score -= 0.15
            if "and" in name_tokens and "and" not in q_tokens:
                score -= 0.02

            if score > best_score:
                best = rec
                best_score = score

        return best, best_score

