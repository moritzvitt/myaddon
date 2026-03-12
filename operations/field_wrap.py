"""Field formatting helpers."""

from __future__ import annotations

from typing import Iterable

LEFT_DIV = '<div style="text-align:left;">'
RIGHT_DIV = "</div>"


def wrap_field_in_left_div(
    col,
    note_ids: Iterable[int],
    *,
    field_name: str,
    dry_run: bool = True,
) -> dict[str, int]:
    updated = 0
    skipped_missing_field = 0
    skipped_empty = 0
    skipped_already_wrapped = 0

    for nid in note_ids:
        note = col.get_note(nid)
        if field_name not in note:
            skipped_missing_field += 1
            continue
        original = note[field_name] or ""
        if not original.strip():
            skipped_empty += 1
            continue
        if LEFT_DIV in original:
            skipped_already_wrapped += 1
            continue
        wrapped = f"{LEFT_DIV}{original}{RIGHT_DIV}"
        if not dry_run:
            note[field_name] = wrapped
            col.update_note(note)
        updated += 1

    return {
        "updated": updated,
        "skipped_missing_field": skipped_missing_field,
        "skipped_empty": skipped_empty,
        "skipped_already_wrapped": skipped_already_wrapped,
        "dry_run": int(dry_run),
    }
