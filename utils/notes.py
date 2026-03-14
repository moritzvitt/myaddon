"""Common note operations."""

from __future__ import annotations

from typing import Iterable, Callable


def remove_tag_from_notes(col, note_ids: Iterable[int], tag: str) -> int:
    removed = 0
    for nid in note_ids:
        note = col.get_note(nid)
        if tag in note.tags:
            note.remove_tag(tag)
            col.update_note(note)
            removed += 1
    return removed


def tag_notes(col, note_ids: Iterable[int], tag: str) -> int:
    added = 0
    for nid in note_ids:
        note = col.get_note(nid)
        if tag not in note.tags:
            note.add_tag(tag)
            col.update_note(note)
            added += 1
    return added


def iter_notes_with_fields(
    col,
    note_ids: Iterable[int],
    required_fields: Iterable[str],
) -> tuple[list[int], int]:
    required = list(required_fields)
    ok_ids: list[int] = []
    missing = 0
    for nid in note_ids:
        note = col.get_note(nid)
        if any(field not in note for field in required):
            missing += 1
            continue
        ok_ids.append(nid)
    return ok_ids, missing


def is_empty_field(note, field_name: str) -> bool:
    return not (note[field_name] or "").strip()


def note_has_flag(col, nid: int, flag: int) -> bool:
    note = col.get_note(nid)
    for cid in note.card_ids():
        card = col.get_card(cid)
        if getattr(card, "flag", 0) == flag:
            return True
    return False


def note_has_tag(col, nid: int, tag: str) -> bool:
    note = col.get_note(nid)
    return tag in note.tags


def note_has_active_card_filtered(col, nid: int, *, ignore_flags: set[int]) -> bool:
    note = col.get_note(nid)
    for cid in note.card_ids():
        card = col.get_card(cid)
        if getattr(card, "queue", None) == -1:
            continue
        if getattr(card, "flag", 0) in ignore_flags:
            continue
        if card.queue in (1, 2, 3):
            return True
    return False


def note_min_due_filtered(col, nid: int, *, ignore_flags: set[int]) -> int:
    note = col.get_note(nid)
    best = 10**12
    for cid in note.card_ids():
        card = col.get_card(cid)
        if getattr(card, "queue", None) == -1:
            continue
        if getattr(card, "flag", 0) in ignore_flags:
            continue
        due = card.due if isinstance(card.due, int) else 10**12
        if due < best:
            best = due
    return best
