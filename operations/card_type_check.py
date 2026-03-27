"""Classify notes as word cards or sentence cards based on cloze hints."""

from __future__ import annotations

import re
from typing import Iterable

from ..utils.cloze import CLOZE_RE
from ..utils.html import strip_html, strip_left_div_wrapper
from ..utils.notes import remove_tag_from_notes
from ..utils.tags import CARD_TYPE_SENTENCE, CARD_TYPE_WORD

WHITESPACE_RE = re.compile(r"\s+")
SENTENCE_PUNCT_RE = re.compile(r"[.!?;:(){}\[\]<>]|[。！？；：]")
COMMA_SPLIT_RE = re.compile(r"\s*,\s*")


def _extract_cloze_hints(text: str) -> list[str]:
    hints: list[str] = []
    for match in CLOZE_RE.finditer(text or ""):
        hint = strip_html(match.group(2) or "")
        hint = strip_left_div_wrapper(hint).strip()
        if hint:
            hints.append(hint)
    return hints


def _normalize_text(text: str) -> str:
    stripped = strip_left_div_wrapper(strip_html(text or ""))
    stripped = WHITESPACE_RE.sub(" ", stripped).strip()
    return stripped.casefold()


def _looks_like_word_hint(hint: str) -> bool:
    normalized = _normalize_text(hint)
    if not normalized:
        return False
    if "\n" in hint or "<br" in hint.lower():
        return False
    if SENTENCE_PUNCT_RE.search(normalized):
        return False

    parts = [part.strip() for part in COMMA_SPLIT_RE.split(normalized) if part.strip()]
    if not parts:
        return False

    total_words = 0
    for part in parts:
        words = [word for word in part.split(" ") if word]
        word_count = len(words) if words else 1
        total_words += word_count
        if word_count > 4:
            return False
        if len(part) > 40:
            return False

    return total_words <= 8


def classify_card_type(
    col,
    note_ids: Iterable[int],
    *,
    cloze_field: str,
    dry_run: bool = True,
) -> dict[str, int]:
    checked = 0
    word_cards = 0
    sentence_cards = 0
    skipped_missing_field = 0
    skipped_empty = 0
    skipped_no_cloze = 0
    skipped_no_hint = 0
    removed_word_tag = 0
    removed_sentence_tag = 0
    added_word_tag = 0
    added_sentence_tag = 0

    if not dry_run:
        removed_word_tag = remove_tag_from_notes(col, note_ids, CARD_TYPE_WORD)
        removed_sentence_tag = remove_tag_from_notes(col, note_ids, CARD_TYPE_SENTENCE)

    for nid in note_ids:
        note = col.get_note(nid)
        if cloze_field not in note:
            skipped_missing_field += 1
            continue

        cloze_value = note[cloze_field] or ""
        if not cloze_value.strip():
            skipped_empty += 1
            continue

        if not list(CLOZE_RE.finditer(cloze_value)):
            skipped_no_cloze += 1
            continue

        hints = _extract_cloze_hints(cloze_value)
        if not hints:
            skipped_no_hint += 1
            continue

        checked += 1
        is_word = all(_looks_like_word_hint(hint) for hint in hints)

        if is_word:
            word_cards += 1
            if not dry_run:
                note.add_tag(CARD_TYPE_WORD)
                col.update_note(note)
                added_word_tag += 1
        else:
            sentence_cards += 1
            if not dry_run:
                note.add_tag(CARD_TYPE_SENTENCE)
                col.update_note(note)
                added_sentence_tag += 1

    return {
        "checked": checked,
        "word_cards": word_cards,
        "sentence_cards": sentence_cards,
        "removed_word_tag": removed_word_tag,
        "removed_sentence_tag": removed_sentence_tag,
        "added_word_tag": added_word_tag,
        "added_sentence_tag": added_sentence_tag,
        "skipped_missing_field": skipped_missing_field,
        "skipped_empty": skipped_empty,
        "skipped_no_cloze": skipped_no_cloze,
        "skipped_no_hint": skipped_no_hint,
        "dry_run": int(dry_run),
    }
