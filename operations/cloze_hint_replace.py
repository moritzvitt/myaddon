"""Replace cloze hints with a field value."""

from __future__ import annotations

import re
from typing import Iterable

from ..config import (
    GREEN_FLAG_SYNONYM_MODE_ALL,
    GREEN_FLAG_SYNONYM_MODE_FIRST,
    GREEN_FLAG_SYNONYM_MODE_FIRST_TWO,
    GREEN_FLAG_SYNONYM_MODE_KEY,
    load_config,
)
from ..utils.synonyms import synonym_hint
from ..utils.tags import STARTUP_REPLACE_HINTS_WITH_SYNONYMS

CLOZE_C1_RE = re.compile(r"\{\{c1::(.*?)(?:::(.*?))?\}\}", re.DOTALL)
GREEN_FLAG = 3


def _prepared_hint_value(hint_field: str, raw_value: str) -> str:
    if hint_field == "Synonyms":
        return synonym_hint(raw_value, limit=2) or ""
    return raw_value


def _prepared_synonym_hint_from_config(raw_value: str) -> str:
    mode = load_config().get(GREEN_FLAG_SYNONYM_MODE_KEY, GREEN_FLAG_SYNONYM_MODE_FIRST_TWO)
    if mode == GREEN_FLAG_SYNONYM_MODE_FIRST:
        limit = 1
    elif mode == GREEN_FLAG_SYNONYM_MODE_ALL:
        limit = None
    else:
        limit = 2
    return synonym_hint(raw_value, limit=limit) or ""


def _green_flagged_card_ids(col) -> list[int]:
    if hasattr(col, "find_cards"):
        return list(col.find_cards("flag:3"))
    if hasattr(col, "findCards"):
        return list(col.findCards("flag:3"))
    return []


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
        hint_value = _prepared_hint_value(hint_field, note[hint_field] or "")
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


def replace_cloze_hints_for_green_flagged_cards(
    col,
    *,
    cloze_field: str = "Cloze",
    synonym_field: str = "Synonyms",
    dry_run: bool = False,
) -> dict[str, int]:
    updated = 0
    skipped_missing_field = 0
    skipped_empty_hint = 0
    skipped_no_change = 0
    tagged = 0
    flags_cleared = 0

    note_to_card_ids: dict[int, list[int]] = {}
    for card_id in _green_flagged_card_ids(col):
        card = col.get_card(card_id)
        if card.user_flag() != GREEN_FLAG:
            continue
        note_to_card_ids.setdefault(int(card.note_id), []).append(int(card_id))

    for note_id, card_ids in note_to_card_ids.items():
        note = col.get_note(note_id)
        if cloze_field not in note or synonym_field not in note:
            skipped_missing_field += 1
            continue

        cloze_value = note[cloze_field] or ""
        hint_value = _prepared_synonym_hint_from_config(note[synonym_field] or "")
        if not hint_value:
            skipped_empty_hint += 1
            continue

        updated_value, count = _replace_hints(cloze_value, hint_value)
        if count == 0 or updated_value == cloze_value:
            skipped_no_change += 1
            continue

        if not dry_run:
            note[cloze_field] = updated_value
            note.add_tag(STARTUP_REPLACE_HINTS_WITH_SYNONYMS)
            col.update_note(note)
            col.set_user_flag_for_cards(0, card_ids)
            tagged += 1
            flags_cleared += len(card_ids)
        updated += 1

    return {
        "updated": updated,
        "skipped_missing_field": skipped_missing_field,
        "skipped_empty_hint": skipped_empty_hint,
        "skipped_no_change": skipped_no_change,
        "tagged": tagged,
        "flags_cleared": flags_cleared,
        "dry_run": int(dry_run),
    }
