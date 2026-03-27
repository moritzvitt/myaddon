"""Classify notes as word cards or sentence cards based on cloze content."""

from __future__ import annotations

import re
from typing import Iterable

from ..utils.cloze import CLOZE_RE
from ..utils.html import strip_html, strip_left_div_wrapper
from ..utils.notes import remove_tag_from_notes
from ..utils.tags import CARD_TYPE_SENTENCE, CARD_TYPE_WORD

WHITESPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^\w\u3040-\u30ff\u4e00-\u9fff]+")
KANA_RE = re.compile(r"[\u3040-\u30ff]")
SENTENCE_HINT_RE = re.compile(r"[\s.,;:!?\"'()[\]{}<>/\\|]|[。！？、…]")


def _extract_hidden_cloze_text(text: str) -> str:
    parts: list[str] = []
    for match in CLOZE_RE.finditer(text or ""):
        inner = strip_html(match.group(1) or "")
        inner = strip_left_div_wrapper(inner).strip()
        if inner:
            parts.append(inner)
    return " ".join(parts).strip()


def _normalize_text(text: str) -> str:
    stripped = strip_left_div_wrapper(strip_html(text or ""))
    stripped = WHITESPACE_RE.sub("", stripped)
    return stripped.casefold()


def _kanji_core(text: str) -> str:
    normalized = _normalize_text(text)
    return KANA_RE.sub("", normalized)


def _shared_edge_length(left: str, right: str) -> int:
    size = min(len(left), len(right))
    count = 0
    for index in range(size):
        if left[index] != right[index]:
            break
        count += 1
    return count


def _looks_like_word_form(hidden_text: str, lemma: str) -> bool:
    hidden = _normalize_text(hidden_text)
    lemma_norm = _normalize_text(lemma)
    if not hidden or not lemma_norm:
        return False
    if hidden == lemma_norm:
        return True

    hidden_compact = PUNCT_RE.sub("", hidden)
    lemma_compact = PUNCT_RE.sub("", lemma_norm)
    if not hidden_compact or not lemma_compact:
        return False
    if hidden_compact == lemma_compact:
        return True

    lemma_kanji = _kanji_core(lemma)
    hidden_kanji = _kanji_core(hidden_text)
    if lemma_kanji and lemma_kanji == hidden_kanji:
        return True

    # Kana-only fallback for simple inflections like たべる -> たべた.
    if not lemma_kanji and not hidden_kanji:
        shared_prefix = _shared_edge_length(lemma_compact, hidden_compact)
        shared_suffix = _shared_edge_length(lemma_compact[::-1], hidden_compact[::-1])
        if max(shared_prefix, shared_suffix) >= max(2, min(len(lemma_compact), len(hidden_compact)) - 1):
            return True

    return False


def classify_card_type(
    col,
    note_ids: Iterable[int],
    *,
    cloze_field: str,
    lemma_field: str,
    dry_run: bool = True,
) -> dict[str, int]:
    checked = 0
    word_cards = 0
    sentence_cards = 0
    skipped_missing_field = 0
    skipped_empty = 0
    skipped_no_cloze = 0
    removed_word_tag = 0
    removed_sentence_tag = 0
    added_word_tag = 0
    added_sentence_tag = 0

    if not dry_run:
        removed_word_tag = remove_tag_from_notes(col, note_ids, CARD_TYPE_WORD)
        removed_sentence_tag = remove_tag_from_notes(col, note_ids, CARD_TYPE_SENTENCE)

    for nid in note_ids:
        note = col.get_note(nid)
        if cloze_field not in note or lemma_field not in note:
            skipped_missing_field += 1
            continue

        cloze_value = note[cloze_field] or ""
        lemma = (note[lemma_field] or "").strip()
        if not cloze_value.strip() or not lemma:
            skipped_empty += 1
            continue

        hidden_text = _extract_hidden_cloze_text(cloze_value)
        if not hidden_text:
            skipped_no_cloze += 1
            continue

        checked += 1
        is_word = _looks_like_word_form(hidden_text, lemma)

        if not is_word and not SENTENCE_HINT_RE.search(hidden_text):
            hidden_kanji = _kanji_core(hidden_text)
            lemma_kanji = _kanji_core(lemma)
            if hidden_kanji and lemma_kanji and hidden_kanji == lemma_kanji:
                is_word = True

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
        "dry_run": int(dry_run),
    }
