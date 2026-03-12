from __future__ import annotations

from aqt import mw
from aqt.qt import *  # type: ignore[import]
from aqt import qconnect

from services.cloze import create_cloze
from services.suspend_duplicates import suspend_duplicates
from services.unsuspend_heisig import unsuspend_heisig_cards_depending_on_cards_in_jp_deck
from services.link_notes import link_notes


def _add_menu_action(label: str, handler) -> None:
    action = QAction(label, mw)
    qconnect(action.triggered, handler)
    mw.form.menuTools.addAction(action)


_add_menu_action("Create Cloze", create_cloze)
_add_menu_action("Suspend Duplicates", suspend_duplicates)
_add_menu_action("Unsuspend Heisig", unsuspend_heisig_cards_depending_on_cards_in_jp_deck)
_add_menu_action("Link Notes", link_notes)
