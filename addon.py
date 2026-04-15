from __future__ import annotations

from aqt import mw, qconnect
from aqt.qt import QAction

from .actions import TOOLS_MENU_ACTIONS
from .dialogs import _tooltip_for_title, open_settings_dialog
from .hooks import register_browser_hooks
from . import shared_menu

_REGISTERED = False
ADDON_MENU_NAME = "Cloze Formatting"


def _add_tools_action(label: str, callback) -> None:
    action = QAction(label, mw)
    tooltip = _tooltip_for_title(label)
    if tooltip:
        action.setToolTip(tooltip)
        action.setStatusTip(tooltip)
    qconnect(action.triggered, callback)
    shared_menu.get_addon_submenu(ADDON_MENU_NAME).addAction(action)


def _register_tools_menu() -> None:
    for label, callback in TOOLS_MENU_ACTIONS:
        _add_tools_action(label, callback)
    shared_menu.add_separator_to_addon_menu(ADDON_MENU_NAME)
    _add_tools_action("Settings", open_settings_dialog)


def register() -> None:
    global _REGISTERED

    if _REGISTERED or mw is None:
        return

    _register_tools_menu()
    register_browser_hooks()
    _REGISTERED = True
