"""Tag notes whose field contains no HTML besides left-align wrapper."""

from __future__ import annotations

from typing import Iterable

from ...utils.html import contains_html, strip_left_div_wrapper
from ...utils.notes import remove_tag_from_notes
from ...utils.tags import NO_HTML


def tag_no_html(
    col,
    note_ids: Iterable[int],
    *,
    field_name: str,
    dry_run: bool = True,
) -> dict[str, int]:
    tagged = 0
    skipped_missing_field = 0
    skipped_empty = 0
    checked = 0

    if not dry_run:
        remove_tag_from_notes(col, note_ids, NO_HTML)

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

        stripped = strip_left_div_wrapper(value)
        if not contains_html(stripped):
            if not dry_run:
                note.add_tag(NO_HTML)
                col.update_note(note)
            tagged += 1

    return {
        "checked": checked,
        "tagged": tagged,
        "skipped_missing_field": skipped_missing_field,
        "skipped_empty": skipped_empty,
        "dry_run": int(dry_run),
    }
