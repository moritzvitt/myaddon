from __future__ import annotations

from aqt import mw, qconnect
from aqt.qt import QAction

from .actions import TOOLS_MENU_ACTIONS
from .hooks import register_browser_hooks

_REGISTERED = False


def _add_tools_action(label: str, callback) -> None:
    action = QAction(label, mw)
    qconnect(action.triggered, callback)
    mw.form.menuTools.addAction(action)


def _register_tools_menu() -> None:
    for label, callback in TOOLS_MENU_ACTIONS:
        _add_tools_action(label, callback)


def register() -> None:
    global _REGISTERED

    if _REGISTERED or mw is None:
        return

    _register_tools_menu()
    register_browser_hooks()
    _REGISTERED = True
