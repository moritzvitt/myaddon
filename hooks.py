from __future__ import annotations

from aqt import gui_hooks

from .actions import run_create_cloze_for_browser, run_replace_cloze_hints_for_browser
from .dialogs import _tooltip_for_title
from . import shared_menu

ADDON_MENU_NAME = "Cloze Formatting"
BROWSER_ACTIONS = (
    ("Apply Cloze Pattern (Selected)", run_create_cloze_for_browser),
    ("Replace Cloze Hints (Selected)", run_replace_cloze_hints_for_browser),
)


def register_browser_hooks() -> None:
    if hasattr(gui_hooks, "browser_menus"):
        gui_hooks.browser_menus.append(_add_browser_menu)
    elif hasattr(gui_hooks, "browser_will_show"):
        gui_hooks.browser_will_show.append(_add_browser_menu)


def _browser_from_hook_args(*args):
    if not args:
        return None
    return args[0]


def _browser_action_exists(browser) -> bool:
    submenu = shared_menu.get_browser_addon_submenu(browser, ADDON_MENU_NAME)
    existing_texts = {action.text() for action in submenu.actions()}
    return all(label in existing_texts for label, _callback in BROWSER_ACTIONS)


def _add_browser_menu(*args) -> None:
    browser = _browser_from_hook_args(*args)
    if browser is None or _browser_action_exists(browser):
        return

    for label, callback in BROWSER_ACTIONS:
        action = shared_menu.add_action_to_browser_addon_menu(
            browser,
            ADDON_MENU_NAME,
            label,
            lambda checked=False, cb=callback: cb(browser),
        )
        tooltip = _tooltip_for_title(label)
        if tooltip:
            action.setToolTip(tooltip)
            action.setStatusTip(tooltip)
