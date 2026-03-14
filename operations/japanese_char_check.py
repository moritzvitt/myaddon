"""Tag notes whose field contains Japanese characters."""

from __future__ import annotations

from typing import Iterable

from ..utils.cloze import contains_japanese
from ..utils.notes import remove_tag_from_notes
from ..utils.tags import CONTAINS_JAPANESE


def tag_contains_japanese(
    col,
    note_ids: Iterable[int],
    *,
    field_name: str,
    dry_run: bool = True,
) -> dict[str, int]:
    checked = 0
    matched = 0
    removed_tag = 0
    added_tag = 0
    skipped_missing_field = 0
    skipped_empty = 0

    if not dry_run:
        removed_tag = remove_tag_from_notes(col, note_ids, CONTAINS_JAPANESE)

    for nid in note_ids:
        note = col.get_note(nid)
        if field_name not in note:
            skipped_missing_field += 1
            continue
        value = note[field_name] or ""
        if not value.strip():
            skipped_empty += 1
            continue
        checked += 1
        if contains_japanese(value):
            matched += 1
            if not dry_run:
                note.add_tag(CONTAINS_JAPANESE)
                col.update_note(note)
                added_tag += 1

    return {
        "checked": checked,
        "matched": matched,
        "removed_tag": removed_tag,
        "added_tag": added_tag,
        "skipped_missing_field": skipped_missing_field,
        "skipped_empty": skipped_empty,
        "dry_run": int(dry_run),
    }
