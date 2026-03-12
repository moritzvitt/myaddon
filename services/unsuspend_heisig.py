from __future__ import annotations

from aqt.utils import showInfo

from ui.dialogs import choose_deck_and_notetype


def unsuspend_heisig_cards_depending_on_cards_in_jp_deck() -> None:
    deck_name, notetype_name = choose_deck_and_notetype()
    if not deck_name or not notetype_name:
        return

    showInfo(
        "Unsuspend Heisig stub executed.\n"
        f"Deck: {deck_name}\n"
        f"Notetype: {notetype_name}"
    )
