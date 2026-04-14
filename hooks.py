from __future__ import annotations

from aqt import gui_hooks
from aqt.qt import QAction

from .actions import run_create_cloze_for_browser
from .dialogs import _tooltip_for_title
from . import shared_menu

ADDON_MENU_NAME = "Cloze Formatting"


def register_browser_hooks() -> None:
    if hasattr(gui_hooks, "browser_menus"):
        gui_hooks.browser_menus.append(_add_browser_menu)
    elif hasattr(gui_hooks, "browser_will_show"):
        gui_hooks.browser_will_show.append(_add_browser_menu)


def _add_browser_menu(browser) -> None:
    action = QAction("Apply Cloze Pattern (Selected)", browser)
    tooltip = _tooltip_for_title("Apply Cloze Pattern (Selected)")
    if tooltip:
        action.setToolTip(tooltip)
        action.setStatusTip(tooltip)
    action.triggered.connect(lambda: run_create_cloze_for_browser(browser))
    shared_menu.get_browser_addon_submenu(browser, ADDON_MENU_NAME).addAction(action)
