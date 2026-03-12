"""Cloze-related operations that work directly on the collection."""

from __future__ import annotations

from typing import Iterable


def _demo_wrap_cloze(value: str) -> str:
    """
    Demo transformation: wrap the whole field in a single cloze if it isn't
    already clozed.
    """
    if "{{c1::" in value:
        return value
    if not value:
        return value
    return "{{c1::" + value + "}}"


def create_cloze(
    col,
    note_ids: Iterable[int],
    *,
    target_field: str = "Cloze",
    dry_run: bool = True,
) -> dict[str, int]:
    """
    Example cloze operation using Anki's collection APIs.

    This is intentionally small and safe; we'll replace the demo transformation
    with your real logic later.
    """
    updated = 0
    skipped_missing_field = 0
    skipped_no_change = 0

    for nid in note_ids:
        note = col.get_note(nid)
        if target_field not in note:
            skipped_missing_field += 1
            continue

        original = note[target_field] or ""
        updated_value = _demo_wrap_cloze(original)
        if updated_value == original:
            skipped_no_change += 1
            continue

        if not dry_run:
            note[target_field] = updated_value
            col.update_note(note)
        updated += 1

    return {
        "updated": updated,
        "skipped_missing_field": skipped_missing_field,
        "skipped_no_change": skipped_no_change,
        "dry_run": int(dry_run),
    }
