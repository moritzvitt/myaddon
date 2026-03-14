"""Remove cloze markup from a field into a target field."""

from __future__ import annotations

from typing import Iterable

from ..utils.cloze import strip_cloze


def strip_cloze_to_field(
    col,
    note_ids: Iterable[int],
    *,
    source_field: str,
    target_field: str,
    dry_run: bool = True,
) -> dict[str, int]:
    updated = 0
    skipped_missing_field = 0
    skipped_target_not_empty = 0
    skipped_empty_source = 0

    for nid in note_ids:
        note = col.get_note(nid)
        if source_field not in note or target_field not in note:
            skipped_missing_field += 1
            continue
        source = note[source_field] or ""
        if not source.strip():
            skipped_empty_source += 1
            continue
        target = note[target_field] or ""
        if target.strip():
            skipped_target_not_empty += 1
            continue

        cleaned = strip_cloze(source)
        if not dry_run:
            note[target_field] = cleaned
            col.update_note(note)
        updated += 1

    return {
        "updated": updated,
        "skipped_missing_field": skipped_missing_field,
        "skipped_target_not_empty": skipped_target_not_empty,
        "skipped_empty_source": skipped_empty_source,
        "dry_run": int(dry_run),
    }
