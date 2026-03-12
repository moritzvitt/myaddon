from __future__ import annotations

import re

from aqt import mw
from aqt.utils import showInfo

from anki import query as anki_query
from anki import notes as anki_notes
from ui.dialogs import ask_yes_no, choose_deck_and_notetype, choose_field_from_notetype


_STRONG_RE = re.compile(r"<strong>(.*?)</strong>", re.IGNORECASE | re.DOTALL)


def create_cloze() -> None:
    deck_name, notetype_name = choose_deck_and_notetype()
    if not deck_name or not notetype_name:
        return

    field_name = choose_field_from_notetype(
        notetype_name,
        "Which field contains the cloze?",
        allow_auto=True,
    )

    is_strong = ask_yes_no("Is the cloze in <strong> tags?")
    if is_strong is None:
        return

    has_multiple_strong = False
    if is_strong:
        multiple = ask_yes_no("Are there multiple <strong> tags (lemma has multiple words)?")
        if multiple is None:
            return
        has_multiple_strong = multiple

    query = f"deck:\"{deck_name}\" note:\"{notetype_name}\""
    note_ids = anki_query.find_notes_by_query(query)

    if not note_ids:
        showInfo("No notes found for selection.")
        return

    updated = 0
    skipped_existing = 0
    skipped_no_strong = 0
    skipped_no_field = 0

    for note_id in note_ids:
        note = anki_notes.get_note(note_id)
        if note is None:
            continue

        field_names = list(note.keys())
        target_field = field_name

        if target_field is None:
            candidates = anki_notes.cloze_field_candidate_names(field_names)
            if candidates:
                target_field = candidates[0]
            else:
                target_field = field_names[0] if field_names else None

        if not target_field or target_field not in note:
            skipped_no_field += 1
            continue

        value = note[target_field] or ""
        if anki_notes.CLOZE_RE.search(value):
            skipped_existing += 1
            continue

        if is_strong:
            matches = list(_STRONG_RE.finditer(value))
            if not matches:
                skipped_no_strong += 1
                continue

            def _replace(match: re.Match[str]) -> str:
                inner = match.group(1)
                return f"{{{{c1::{inner}}}}}"

            if has_multiple_strong:
                new_value = _STRONG_RE.sub(_replace, value)
            else:
                first = matches[0]
                new_value = value[: first.start()] + _replace(first) + value[first.end() :]
                new_value = _STRONG_RE.sub(lambda m: m.group(1), new_value)

            if new_value != value:
                note[target_field] = new_value
                if mw is not None:
                    mw.col.update_note(note)
                updated += 1
        else:
            skipped_no_strong += 1

    showInfo(
        "Create Cloze finished.\n"
        f"Updated: {updated}\n"
        f"Skipped (existing cloze): {skipped_existing}\n"
        f"Skipped (no <strong> tags): {skipped_no_strong}\n"
        f"Skipped (missing field): {skipped_no_field}"
    )
