"""HTML helpers."""

from __future__ import annotations

import re

LEFT_DIV_RE = re.compile(
    r"^\s*<div\s+style=\"text-align:left;\">(.*)</div>\s*$",
    re.IGNORECASE | re.DOTALL,
)
HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    return HTML_TAG_RE.sub("", text or "")


def strip_left_div_wrapper(text: str) -> str:
    stripped = (text or "").strip()
    match = LEFT_DIV_RE.match(stripped)
    if match:
        return match.group(1)
    return stripped


def contains_html(text: str) -> bool:
    return bool(HTML_TAG_RE.search(text or ""))
