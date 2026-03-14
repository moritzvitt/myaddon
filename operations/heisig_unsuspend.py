"""Unsuspend Heisig cards based on JP deck lemmas."""

from __future__ import annotations

import re
from typing import Iterable

from ..utils.config import JP_DECK, HEISIG_DECK, HEISIG_KANJI_FIELD
from ..utils.tags import HEISIG_UNSUSPEND

KANJI_RE = re.compile(r"[\u4e00-\u9fff]")


def _extract_kanji(text: str) -> set[str]:
    return set(KANJI_RE.findall(text or ""))


def unsuspend_heisig_by_jp_lemmas(
    col,
    *,
    jp_deck: str = JP_DECK,
    jp_lemma_field: str = "Lemma",
    heisig_deck: str = HEISIG_DECK,
    heisig_kanji_field: str = HEISIG_KANJI_FIELD,
    tag: str = HEISIG_UNSUSPEND,
    dry_run: bool = True,
) -> dict[str, int]:
    jp_query = f'deck:"{jp_deck}" (is:review OR is:learn)'
    jp_card_ids = col.find_cards(jp_query)
    if not jp_card_ids:
        return {
            "jp_cards": 0,
            "jp_notes": 0,
            "kanji_collected": 0,
            "heisig_notes_scanned": 0,
            "heisig_notes_matched": 0,
            "heisig_cards_unsuspended": 0,
            "dry_run": int(dry_run),
        }

    jp_note_ids = {col.get_card(cid).note().id for cid in jp_card_ids}
    kanji_pool: set[str] = set()
    skipped_missing_lemma = 0
    for nid in jp_note_ids:
        note = col.get_note(nid)
        if jp_lemma_field not in note:
            skipped_missing_lemma += 1
            continue
        kanji_pool.update(_extract_kanji(note[jp_lemma_field] or ""))

    heisig_query = f'deck:"{heisig_deck}"'
    heisig_note_ids = col.find_notes(heisig_query)

    matched_notes: list[int] = []
    for nid in heisig_note_ids:
        note = col.get_note(nid)
        if heisig_kanji_field not in note:
            continue
        kanji_value = note[heisig_kanji_field] or ""
        if any(k in kanji_value for k in kanji_pool):
            matched_notes.append(nid)
            if not dry_run:
                note.add_tag(tag)
                col.update_note(note)

    card_ids_to_unsuspend: list[int] = []
    for nid in matched_notes:
        note = col.get_note(nid)
        card_ids_to_unsuspend.extend(note.card_ids())

    if not dry_run and card_ids_to_unsuspend:
        sched = getattr(col, "sched", None)
        if sched is not None and hasattr(sched, "unsuspend_cards"):
            sched.unsuspend_cards(card_ids_to_unsuspend)
        else:
            for cid in card_ids_to_unsuspend:
                card = col.get_card(cid)
                if getattr(card, "queue", None) == -1:
                    card.queue = 0
                    col.update_card(card)

    return {
        "jp_cards": len(jp_card_ids),
        "jp_notes": len(jp_note_ids),
        "kanji_collected": len(kanji_pool),
        "skipped_missing_lemma": skipped_missing_lemma,
        "heisig_notes_scanned": len(heisig_note_ids),
        "heisig_notes_matched": len(matched_notes),
        "heisig_cards_unsuspended": len(card_ids_to_unsuspend),
        "dry_run": int(dry_run),
    }
