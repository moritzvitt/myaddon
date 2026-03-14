"""Replace cloze hints with a field value."""

from __future__ import annotations

import re
from typing import Iterable

from ..utils.cloze import strip_cloze

CLOZE_C1_RE = re.compile(r"\{\{c1::(.*?)(?:::(.*?))?\}\}", re.DOTALL)


def replace_cloze_hints(
    col,
    note_ids: Iterable[int],
    *,
    cloze_field: str = "Cloze",
    hint_field: str = "Word Definition",
    dry_run: bool = True,
) -> dict[str, int]:
    updated = 0
    skipped_missing_field = 0
    skipped_empty_hint = 0
    skipped_no_change = 0

    for nid in note_ids:
        note = col.get_note(nid)
        if cloze_field not in note or hint_field not in note:
            skipped_missing_field += 1
            continue
        cloze_value = note[cloze_field] or ""
        hint_value = note[hint_field] or ""
        if not hint_value:
            skipped_empty_hint += 1
            continue

        updated_value, count = _replace_hints(cloze_value, hint_value)
        if count == 0 or updated_value == cloze_value:
            skipped_no_change += 1
            continue
        if not dry_run:
            note[cloze_field] = updated_value
            col.update_note(note)
        updated += 1

    return {
        "updated": updated,
        "skipped_missing_field": skipped_missing_field,
        "skipped_empty_hint": skipped_empty_hint,
        "skipped_no_change": skipped_no_change,
        "dry_run": int(dry_run),
    }


def _replace_hints(text: str, new_hint: str) -> tuple[str, int]:
    if not text:
        return text, 0

    def _repl(match: re.Match[str]) -> str:
        cloze_text = match.group(1)
        return f"{{{{c1::{cloze_text}::{new_hint}}}}}"

    updated, count = CLOZE_C1_RE.subn(_repl, text)
    return updated, count
