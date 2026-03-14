"""Cloze helpers."""

from __future__ import annotations

import re
from typing import Iterable

CLOZE_RE = re.compile(
    r"\{\{c\d+::(.*?)(?:::(.*?))?(?:::)??\}\}", re.IGNORECASE | re.DOTALL
)


def strip_cloze(text: str) -> str:
    if not text:
        return ""

    def _repl(match: re.Match[str]) -> str:
        return match.group(1)

    return CLOZE_RE.sub(_repl, text)


def longest_substring_match(haystack: str, needle: str) -> str | None:
    if not haystack or not needle:
        return None
    best = ""
    needle_len = len(needle)
    for start in range(needle_len):
        for end in range(start + 1, needle_len + 1):
            if end - start <= len(best):
                continue
            chunk = needle[start:end]
            if chunk and chunk in haystack:
                best = chunk
    return best or None


def contains_japanese(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text or ""))
