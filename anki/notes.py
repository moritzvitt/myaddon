from __future__ import annotations

import re
from aqt import mw


CLOZE_RE = re.compile(r"\{\{c\d+::.+?\}\}")


def get_note_field_names(note_id: int) -> list[str]:
    if mw is None:
        return []
    note = mw.col.get_note(note_id)
    return list(note.keys())


def get_note(note_id: int):
    if mw is None:
        return None
    return mw.col.get_note(note_id)


def get_note_type_field_names(notetype_name: str) -> list[str]:
    if mw is None:
        return []
    model = mw.col.models.by_name(notetype_name)
    if not model:
        return []
    return [f["name"] for f in model.get("flds", [])]


def note_has_cloze(note_id: int, field_name: str | None = None) -> bool:
    if mw is None:
        return False
    note = mw.col.get_note(note_id)
    if field_name:
        return bool(CLOZE_RE.search(note[field_name] or ""))
    for name in note.keys():
        if CLOZE_RE.search(note[name] or ""):
            return True
    return False


def first_field_name(note_id: int) -> str | None:
    names = get_note_field_names(note_id)
    return names[0] if names else None


def cloze_field_candidate_names(field_names: list[str]) -> list[str]:
    names_lower = {n.lower(): n for n in field_names}
    candidates = []
    if "cloze" in names_lower:
        candidates.append(names_lower["cloze"])
    if "cloze" not in names_lower and "Cloze" in field_names:
        candidates.append("Cloze")
    return candidates
