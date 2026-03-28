"""HTML cleanup helpers."""

from __future__ import annotations

import re
from typing import Iterable

BR_RUN_RE = re.compile(r"(?:<br\s*/?>\s*){4,}", re.IGNORECASE)


def _collapse_br_runs(value: str) -> tuple[str, bool]:
    if not value:
        return value, False
    changed = False

    def _repl(match: re.Match[str]) -> str:
        nonlocal changed
        changed = True
        return "<br><br><br>"

    updated = BR_RUN_RE.sub(_repl, value)
    return updated, changed


def cleanup_br_runs(
    col,
    note_ids: Iterable[int],
    *,
    field_name: str,
    dry_run: bool = True,
) -> dict[str, int]:
    updated = 0
    skipped_missing_field = 0
    skipped_empty = 0
    skipped_no_change = 0

    for nid in note_ids:
        note = col.get_note(nid)
        if field_name not in note:
            skipped_missing_field += 1
            continue
        original = note[field_name] or ""
        if not original.strip():
            skipped_empty += 1
            continue
        updated_value, changed = _collapse_br_runs(original)
        if not changed:
            skipped_no_change += 1
            continue
        if not dry_run:
            note[field_name] = updated_value
            col.update_note(note)
        updated += 1

    return {
        "updated": updated,
        "skipped_missing_field": skipped_missing_field,
        "skipped_empty": skipped_empty,
        "skipped_no_change": skipped_no_change,
        "dry_run": int(dry_run),
    }
