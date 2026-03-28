"""Overwrite one field with the content of another."""

from __future__ import annotations

from ...utils.notes import iter_notes_with_fields


def overwrite_field_from_field(
    col,
    note_ids: list[int],
    *,
    source_field: str,
    target_field: str,
    dry_run: bool = False,
) -> dict[str, int]:
    ok_ids, skipped_missing_field = iter_notes_with_fields(
        col, note_ids, [source_field, target_field]
    )
    overwritten = 0
    for nid in ok_ids:
        note = col.get_note(nid)
        source = note[source_field] or ""
        if not dry_run:
            note[target_field] = source
            col.update_note(note)
        overwritten += 1
    return {
        "overwritten": overwritten,
        "skipped_missing_field": skipped_missing_field,
    }
