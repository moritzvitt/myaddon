from __future__ import annotations

from html import unescape
import re

LIST_ITEM_RE = re.compile(r"<li\b[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def _clean_synonym_text(value: str) -> str:
    stripped = HTML_TAG_RE.sub(" ", value)
    return WHITESPACE_RE.sub(" ", stripped).strip(" ,;:-")


def synonym_items(raw_value: str) -> list[str]:
    if not raw_value:
        return []

    decoded = unescape(raw_value)
    items = [_clean_synonym_text(match) for match in LIST_ITEM_RE.findall(decoded)]
    items = [item for item in items if item]
    if items:
        return items

    fallback = decoded
    for needle in ("<br>", "<br/>", "<br />", "</li>", "</ul>", "</ol>", "</p>"):
        fallback = fallback.replace(needle, "\n")
    fallback = fallback.replace("<li>", "")
    fallback = fallback.replace("<ul>", "")
    fallback = fallback.replace("<ol>", "")
    fallback = fallback.replace("<p>", "")
    lines = [_clean_synonym_text(line) for line in fallback.splitlines()]
    return [line for line in lines if line]


def synonym_hint(raw_value: str, limit: int | None = None) -> str | None:
    items = synonym_items(raw_value)
    if limit is not None:
        items = items[:limit]
    items = [item for item in items if item]
    if not items:
        return None
    return ", ".join(items)
