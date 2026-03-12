from __future__ import annotations

from aqt import mw


def find_notes_by_query(query: str) -> list[int]:
    if mw is None:
        return []
    return list(mw.col.find_notes(query))
