from __future__ import annotations

from aqt import mw, qconnect
from aqt.qt import QAction, QMenu

from .actions import (
    ADVANCED_TOOLS_MENU_ACTIONS,
    BROWSER_ADVANCED_ACTIONS,
    DIAGNOSTICS_TOOLS_MENU_ACTIONS,
    MAIN_TOOLS_MENU_ACTIONS,
)
from .hooks import register_browser_hooks, register_profile_hooks

_REGISTERED = False


def _add_tools_action(label: str, callback) -> None:
    action = QAction(label, mw)
    qconnect(action.triggered, callback)
    mw.form.menuTools.addAction(action)


def _register_tools_menu() -> None:
    for label, callback in MAIN_TOOLS_MENU_ACTIONS:
        _add_tools_action(label, callback)

    advanced_menu = QMenu("Advanced", mw)
    for label, callback in ADVANCED_TOOLS_MENU_ACTIONS:
        if callback is None:
            continue
        action = QAction(label, mw)
        qconnect(action.triggered, callback)
        advanced_menu.addAction(action)
    mw.form.menuTools.addMenu(advanced_menu)

    diagnostics_menu = QMenu("Diagnostics", mw)
    for label, callback in DIAGNOSTICS_TOOLS_MENU_ACTIONS:
        action = QAction(label, mw)
        qconnect(action.triggered, callback)
        diagnostics_menu.addAction(action)
    mw.form.menuTools.addMenu(diagnostics_menu)


def register() -> None:
    global _REGISTERED

    if _REGISTERED or mw is None:
        return

    _register_tools_menu()
    register_browser_hooks()
    register_profile_hooks()
    _REGISTERED = True
