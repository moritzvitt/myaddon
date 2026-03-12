from __future__ import annotations

from aqt.utils import showInfo

from ui.dialogs import choose_deck_and_notetype


def link_notes() -> None:
    deck_name, notetype_name = choose_deck_and_notetype()
    if not deck_name or not notetype_name:
        return

    showInfo(
        "Link Notes stub executed.\n"
        f"Deck: {deck_name}\n"
        f"Notetype: {notetype_name}"
    )
