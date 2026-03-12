"""Cloze-related operations that work directly on the collection."""

from __future__ import annotations

import re
from typing import Iterable

STRONG_RE = re.compile(r"<strong>\s*(.*?)\s*</strong>", re.IGNORECASE | re.DOTALL)
TOKEN_SPLIT_RE = re.compile(r"[^\w\u3040-\u30ff\u4e00-\u9fff]+")
CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")

TAG_EXISTING_CLOZE = "meta::cloze_existing"


def _wrap_strong_cloze(value: str, hint: str) -> str | None:
    match = STRONG_RE.search(value or "")
    if not match:
        return None
    inner = match.group(1)
    if not inner.strip():
        return None
    cloze = f"{{{{c1::<strong>{inner}</strong>::{hint}}}}}"
    return value[: match.start()] + cloze + value[match.end() :]


def _wrap_match_cloze(value: str, match_text: str, hint: str) -> str:
    return value.replace(match_text, f"{{{{c1::{match_text}::{hint}}}}}", 1)


def _find_match_text(value: str, lemma: str) -> tuple[str, str] | None:
    if not value or not lemma:
        return None
    exact_re = re.compile(re.escape(lemma), re.IGNORECASE)
    exact = exact_re.search(value)
    if exact:
        return value[exact.start() : exact.end()], "exact"

    tokens = [t for t in TOKEN_SPLIT_RE.split(lemma) if len(t) >= 3]
    if not tokens:
        pass
    else:
        tokens.sort(key=len, reverse=True)
        token_re = re.compile(re.escape(tokens[0]), re.IGNORECASE)
        token = token_re.search(value)
        if token:
            return value[token.start() : token.end()], "longest_token"

    cjk_chars = CJK_CHAR_RE.findall(lemma)
    if len(cjk_chars) >= 2:
        prefix = "".join(cjk_chars[:2])
        prefix_re = re.compile(re.escape(prefix))
        prefix_match = prefix_re.search(value)
        if prefix_match:
            return value[prefix_match.start() : prefix_match.end()], "cjk_prefix"
    elif len(cjk_chars) == 1:
        single = cjk_chars[0]
        single_re = re.compile(re.escape(single))
        single_match = single_re.search(value)
        if single_match:
            return value[single_match.start() : single_match.end()], "cjk_single"
    return None


def create_cloze(
    col,
    note_ids: Iterable[int],
    *,
    target_field: str = "Cloze",
    lemma_field: str = "Lemma",
    hint_field: str = "Word Definition",
    dry_run: bool = True,
) -> dict[str, int]:
    """
    Example cloze operation using Anki's collection APIs.

    This applies a cloze to <strong> tags when present, otherwise tries to
    match the lemma or its longest token.
    """
    updated = 0
    skipped_missing_field = 0
    skipped_no_change = 0
    tagged_no_strong = 0
    tagged_failed = 0
    tagged_existing = 0

    for nid in note_ids:
        note = col.get_note(nid)
        if target_field not in note or lemma_field not in note or hint_field not in note:
            skipped_missing_field += 1
            continue

        original = note[target_field] or ""
        if "{{c1::" in original:
            skipped_no_change += 1
            if not dry_run:
                note.add_tag(TAG_EXISTING_CLOZE)
                col.update_note(note)
            tagged_existing += 1
            continue

        lemma = (note[lemma_field] or "").strip()
        hint = (note[hint_field] or "").strip()
        updated_value = _wrap_strong_cloze(original, hint)
        no_strong = updated_value is None

        if updated_value is None:
            match_result = _find_match_text(original, lemma)
            if match_result:
                match_text, match_kind = match_result
                updated_value = _wrap_match_cloze(original, match_text, hint)
                if match_kind in {"cjk_prefix", "cjk_single"} and not dry_run:
                    note.add_tag("meta::incorrect_parsing")

        if updated_value is None or updated_value == original:
            if not dry_run:
                note.add_tag("meta::cloze_failed")
                col.update_note(note)
            tagged_failed += 1
            continue

        if not dry_run:
            note[target_field] = updated_value
            if no_strong:
                note.add_tag("meta::cloze_no_strong")
                tagged_no_strong += 1
            col.update_note(note)
        updated += 1
        if no_strong:
            tagged_no_strong += 1

    return {
        "updated": updated,
        "skipped_missing_field": skipped_missing_field,
        "skipped_no_change": skipped_no_change,
        "tagged_no_strong": tagged_no_strong,
        "tagged_failed": tagged_failed,
        "tagged_existing": tagged_existing,
        "dry_run": int(dry_run),
    }
