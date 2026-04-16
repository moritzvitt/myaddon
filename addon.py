from __future__ import annotations

from aqt import gui_hooks, mw, qconnect
from aqt.qt import QAction

from .actions import TOOLS_MENU_ACTIONS, run_startup_green_flag_replacement
from .dialogs import _tooltip_for_title, open_settings_dialog
from .hooks import register_browser_hooks
from . import shared_menu

_REGISTERED = False
_STARTUP_HOOK_REGISTERED = False
_STARTUP_TASK_RAN = False
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


def _run_startup_tasks(*_args) -> None:
    global _STARTUP_TASK_RAN
    if _STARTUP_TASK_RAN:
        return
    if mw is None or getattr(mw, "col", None) is None:
        return
    _STARTUP_TASK_RAN = True
    run_startup_green_flag_replacement()


def _register_startup_hook() -> None:
    global _STARTUP_HOOK_REGISTERED
    if _STARTUP_HOOK_REGISTERED:
        return
    if hasattr(gui_hooks, "profile_did_open"):
        gui_hooks.profile_did_open.append(_run_startup_tasks)
    elif hasattr(gui_hooks, "main_window_did_init"):
        gui_hooks.main_window_did_init.append(_run_startup_tasks)
    _STARTUP_HOOK_REGISTERED = True


def register() -> None:
    global _REGISTERED

    if _REGISTERED or mw is None:
        return

    _register_tools_menu()
    register_browser_hooks()
    _register_startup_hook()
    _REGISTERED = True
