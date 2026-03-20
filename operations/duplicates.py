"""Duplicate lemma handling."""

from __future__ import annotations

from collections import defaultdict

from ..utils.tags import DUPLICATES_FAILED, DUPLICATES_MISSING_LEMMA


def _suspend_note_cards(col, nid: int, *, dry_run: bool) -> int:
    note = col.get_note(nid)
    card_ids = note.card_ids()
    if not card_ids:
        return 0
    if dry_run:
        return len(card_ids)
    sched = getattr(col, "sched", None)
    if sched is not None and hasattr(sched, "suspend_cards"):
        sched.suspend_cards(card_ids)
    else:
        for cid in card_ids:
            card = col.get_card(cid)
            if getattr(card, "queue", None) != -1:
                card.queue = -1
                col.update_card(card)
    return len(card_ids)


def _tag_note(col, nid: int, tag: str, *, dry_run: bool) -> None:
    if dry_run:
        return
    note = col.get_note(nid)
    note.add_tag(tag)
    col.update_note(note)


def suspend_duplicates(
    col,
    *,
    query: str = (
        'deck:JP -tag:meta::retired is:new "note:Moritz Language Reactor" '
        "-(is:suspended flag:1) -(is:suspended flag:2) -(is:suspended flag:4) "
        "-(is:suspended flag:5) -(is:suspended flag:6) -(is:suspended flag:7) -tag:marked"
        "-tag:marked"
    ),
    lemma_field: str = "Lemma",
    dry_run: bool = True,
) -> dict[str, int]:
    note_ids: list[int] = col.find_notes(query)
    notes_by_lemma: dict[str, list[int]] = defaultdict(list)
    skipped_missing_lemma = 0
    tagged_missing_lemma = 0
    tagged_failed = 0

    for nid in note_ids:
        try:
            note = col.get_note(nid)
            if lemma_field not in note:
                skipped_missing_lemma += 1
                _tag_note(col, nid, DUPLICATES_MISSING_LEMMA, dry_run=dry_run)
                tagged_missing_lemma += 1
                continue
            lemma = (note[lemma_field] or "").strip()
            if not lemma:
                skipped_missing_lemma += 1
                _tag_note(col, nid, DUPLICATES_MISSING_LEMMA, dry_run=dry_run)
                tagged_missing_lemma += 1
                continue
            notes_by_lemma[lemma].append(nid)
        except Exception:
            _tag_note(col, nid, DUPLICATES_FAILED, dry_run=dry_run)
            tagged_failed += 1
            continue

    duplicate_groups = [nids for nids in notes_by_lemma.values() if len(nids) > 1]
    suspended_notes = 0
    suspended_cards = 0

    for nids in duplicate_groups:
        try:
            keep_nid = nids[0]
            for nid in nids[1:]:
                changed = _suspend_note_cards(col, nid, dry_run=dry_run)
                if changed == 0:
                    _tag_note(col, nid, DUPLICATES_FAILED, dry_run=dry_run)
                    tagged_failed += 1
                    continue
                suspended_cards += changed
                suspended_notes += 1
        except Exception:
            for nid in nids:
                _tag_note(col, nid, DUPLICATES_FAILED, dry_run=dry_run)
            tagged_failed += len(nids)
            continue

    return {
        "total_notes": len(note_ids),
        "duplicate_groups": len(duplicate_groups),
        "suspended_notes": suspended_notes,
        "suspended_cards": suspended_cards,
        "skipped_missing_lemma": skipped_missing_lemma,
        "tagged_missing_lemma": tagged_missing_lemma,
        "tagged_failed": tagged_failed,
        "dry_run": int(dry_run),
    }
