"""Populate Heisig Link field with JP examples."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from ...utils.cloze import strip_cloze
from ...utils.html import strip_html
from ...utils.config import (
    HEISIG_DECK,
    HEISIG_KANJI_FIELD,
    HEISIG_LINK_FIELD,
    HEISIG_NOTE_TYPE,
    JP_CLOZE_FIELD,
    JP_DECK,
    JP_LEMMA_FIELD,
    JP_LEARNING_NOTETYPE,
)
from ...utils.notes import (
    note_has_active_card_filtered,
    note_has_flag,
    note_has_tag,
    note_min_due_filtered,
)

KANJI_RE = re.compile(r"[\u4e00-\u9fff]")


def _extract_kanji(text: str) -> set[str]:
    return set(KANJI_RE.findall(text or ""))


def _sanitize_link_text(text: str) -> str:
    return (text or "").replace("[", "(").replace("]", ")").replace("|", "/").strip()


def _truncate_sentence(text: str, focus_chars: Iterable[str], *, max_len: int = 20) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    focus_char = ""
    for ch in focus_chars:
        if ch and ch in text:
            focus_char = ch
            break
    if focus_char:
        idx = text.find(focus_char)
        if idx != -1:
            start = max(0, idx - 5)
            end = min(len(text), idx + len(focus_char) + 5)
            window = text[start:end]
            if len(window) > max_len:
                window = window[:max_len]
            if start > 0:
                window = "..." + window
            if end < len(text):
                window = window + "..."
            return window[: max_len + 3]
    # Fallback: trim from end
    return text[:max_len] + "..."

def _note_status(col, nid: int) -> str | None:
    note = col.get_note(nid)
    statuses = set()
    for cid in note.card_ids():
        card = col.get_card(cid)
        # queue: -1 suspended, 0 new, 1 learning, 2 review, 3 relearning
        if card.queue in (1, 2, 3):
            statuses.add("learning")
        elif card.queue == 0:
            statuses.add("new")
    if "learning" in statuses:
        return "learning"
    if "new" in statuses:
        return "new"
    return None


def _note_min_due(col, nid: int) -> int:
    note = col.get_note(nid)
    best = 10**12
    for cid in note.card_ids():
        card = col.get_card(cid)
        due = card.due if isinstance(card.due, int) else 10**12
        if due < best:
            best = due
    return best


def populate_heisig_links_by_jp_lemmas(
    col,
    *,
    jp_deck: str = JP_DECK,
    jp_lemma_field: str = JP_LEMMA_FIELD,
    jp_sentence_field: str = JP_CLOZE_FIELD,
    jp_learning_notetype: str = JP_LEARNING_NOTETYPE,
    heisig_deck: str = HEISIG_DECK,
    heisig_note_type: str = HEISIG_NOTE_TYPE,
    heisig_kanji_field: str = HEISIG_KANJI_FIELD,
    heisig_link_field: str = HEISIG_LINK_FIELD,
    dry_run: bool = True,
) -> dict[str, int]:
    jp_query = f'deck:"{jp_deck}" or (tag:meta::retired is:suspended)'
    jp_note_ids = col.find_notes(jp_query)

    lemma_by_note: dict[int, str] = {}
    sentence_by_note: dict[int, str] = {}
    status_by_note: dict[int, str] = {}
    due_by_note: dict[int, int] = {}
    notetype_by_note: dict[int, str] = {}
    kanji_to_lemma_notes: dict[str, set[int]] = defaultdict(set)
    kanji_to_sentence_notes: dict[str, set[int]] = defaultdict(set)
    skipped_missing_fields = 0

    for nid in jp_note_ids:
        note = col.get_note(nid)
        if jp_lemma_field not in note:
            skipped_missing_fields += 1
            continue
        lemma = (note[jp_lemma_field] or "").strip()
        if jp_sentence_field in note:
            sentence_raw = note[jp_sentence_field] or ""
            sentence = strip_html(strip_cloze(sentence_raw)).strip()
        else:
            sentence = ""
        lemma_by_note[nid] = lemma
        sentence_by_note[nid] = sentence
        notetype_by_note[nid] = note.model().get("name", "")
        status = _note_status(col, nid)
        if status:
            status_by_note[nid] = status
        due_by_note[nid] = _note_min_due(col, nid)

        for k in _extract_kanji(lemma):
            kanji_to_lemma_notes[k].add(nid)
        for k in _extract_kanji(sentence):
            kanji_to_sentence_notes[k].add(nid)

    heisig_query = f'deck:"{heisig_deck}" note:"{heisig_note_type}"'
    heisig_note_ids = col.find_notes(heisig_query)

    updated = 0
    skipped_missing_fields_heisig = 0

    for nid in heisig_note_ids:
        note = col.get_note(nid)
        if heisig_kanji_field not in note or heisig_link_field not in note:
            skipped_missing_fields_heisig += 1
            continue

        kanji_value = note[heisig_kanji_field] or ""
        kanji_chars = _extract_kanji(kanji_value)
        if not kanji_chars:
            continue

        learning_ids: set[int] = set()
        not_learning_ids: set[int] = set()
        sentence_ids_all: set[int] = set()
        sentence_ids_learning: set[int] = set()

        for k in kanji_chars:
            for nid2 in kanji_to_lemma_notes.get(k, set()):
                status = status_by_note.get(nid2)
                if status == "learning" and notetype_by_note.get(nid2) == jp_learning_notetype:
                    learning_ids.add(nid2)
                else:
                    not_learning_ids.add(nid2)
            for nid2 in kanji_to_sentence_notes.get(k, set()):
                sentence_ids_all.add(nid2)

        def _sort_key(nid2: int) -> int:
            return due_by_note.get(nid2, 10**12)

        learning_sorted = sorted(learning_ids, key=_sort_key)
        not_learning_sorted = sorted(not_learning_ids, key=_sort_key)
        sentence_sorted_all = sorted(sentence_ids_all, key=_sort_key)

        def _build_links_inline(note_ids: list[int], text_by_note: dict[int, str]) -> str:
            links: list[str] = []
            for nid2 in note_ids:
                text = _sanitize_link_text(text_by_note.get(nid2, ""))
                if not text:
                    continue
                links.append(f"[{text}|nid{nid2}]")
            return " ".join(links)

        # Block 1: all learning examples, one line
        learning_block = _build_links_inline(learning_sorted, lemma_by_note)

        # Block 2: learning sentences with filters, max 4
        ignore_flags = {1, 5}
        for nid2 in sentence_sorted_all:
            if note_has_active_card_filtered(col, nid2, ignore_flags=ignore_flags):
                sentence_ids_learning.add(nid2)
            elif note_has_tag(col, nid2, "meta::retired"):
                # Include retired suspended notes in sentence block.
                sentence_ids_learning.add(nid2)
        sentence_learning_sorted = sorted(
            sentence_ids_learning,
            key=lambda nid2: note_min_due_filtered(col, nid2, ignore_flags=ignore_flags),
        )

        # Deduplicate by sentence content, keep first occurrence (lowest due).
        seen_sentences: set[str] = set()
        sentence_learning_unique: list[int] = []
        for nid2 in sentence_learning_sorted:
            text = (sentence_by_note.get(nid2, "") or "").strip()
            if not text or text in seen_sentences:
                continue
            seen_sentences.add(text)
            sentence_learning_unique.append(nid2)
            if len(sentence_learning_unique) >= 4:
                break

        def _build_links_multiline(
            note_ids: list[int],
            text_by_note: dict[int, str],
            focus_chars: Iterable[str],
        ) -> str:
            links: list[str] = []
            for nid2 in note_ids:
                raw_text = text_by_note.get(nid2, "")
                text = _sanitize_link_text(
                    _truncate_sentence(raw_text, focus_chars, max_len=20)
                )
                if not text:
                    continue
                links.append(f"[{text}|nid{nid2}]")
            return "<br>".join(links)

        sentence_learning_block = _build_links_multiline(
            sentence_learning_unique, sentence_by_note, kanji_chars
        )

        # Block 3: lemmas not learning, sorted by due, max 10, unique lemma text
        seen_lemmas: set[str] = set()
        not_learning_unique: list[int] = []
        for nid2 in not_learning_sorted:
            lemma_text = (lemma_by_note.get(nid2, "") or "").strip()
            if not lemma_text or lemma_text in seen_lemmas:
                continue
            if notetype_by_note.get(nid2) == "Moritz Language Reactor Phrase":
                continue
            if note_has_flag(col, nid2, 4):
                continue
            seen_lemmas.add(lemma_text)
            not_learning_unique.append(nid2)
            if len(not_learning_unique) >= 10:
                break
        not_learning_block = _build_links_inline(not_learning_unique, lemma_by_note)

        # Block 4: sentences across JP, max 2 per lemma, max 10 total, by due
        # Block 4 disabled for now.
        # sentence_block = ""

        blocks = []
        if learning_block:
            blocks.append(learning_block)
        if sentence_learning_block:
            blocks.append(sentence_learning_block)
        if not_learning_block:
            blocks.append(not_learning_block)

        updated_value = "<br><br>".join(blocks)
        updated_value = f'<div style="text-align:left;">{updated_value}</div>'

        if not dry_run:
            note[heisig_link_field] = updated_value
            col.update_note(note)
        updated += 1

    return {
        "jp_notes": len(jp_note_ids),
        "jp_notes_with_status": len(status_by_note),
        "heisig_notes": len(heisig_note_ids),
        "updated": updated,
        "skipped_missing_fields_jp": skipped_missing_fields,
        "skipped_missing_fields_heisig": skipped_missing_fields_heisig,
        "dry_run": int(dry_run),
    }
