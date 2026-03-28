from __future__ import annotations

import re

from aqt import gui_hooks, mw
from aqt.qt import QAction, QMenu
from aqt.utils import tooltip

from .actions import BROWSER_ADVANCED_ACTIONS, run_create_cloze_for_browser
from .addon_config import get_addon_config
from .operations.hidden.field_wrap import wrap_field_in_left_div
from .utils.notes import remove_tag_from_notes, tag_notes

LIMIT_RE = re.compile(r"limit:(\d+)", re.IGNORECASE)


def apply_card_limit(context) -> None:
    if context.browser.table.is_notes_mode():
        return

    search = context.search or ""
    match = LIMIT_RE.search(search)
    if not match:
        return
    limit = int(match.group(1))
    search = LIMIT_RE.sub("", search).strip()
    search = re.sub(r"\s{2,}", " ", search)
    if not search:
        search = "*"

    if limit <= 0:
        context.search = search
        return

    card_ids = list(context.browser.col.find_cards(search, order="c.due asc"))
    context.ids = card_ids[:limit]
    context.search = search


def auto_wrap_left_div_on_startup() -> None:
    notetype_name = "Moritz Language Reactor"
    query = f'note:"{notetype_name}"'
    note_ids = mw.col.find_notes(query)
    if not note_ids:
        return
    wrap_field_in_left_div(mw.col, note_ids, field_name="Notes", dry_run=False)
    wrap_field_in_left_div(mw.col, note_ids, field_name="Grammar", dry_run=False)
    tooltip("applied left-div to Notes & Grammar")


def auto_tag_preview_on_startup() -> None:
    config = get_addon_config()
    query = str(config.get("preview_query") or "").strip()
    tag = str(config.get("preview_tag") or "").strip()
    try:
        limit = max(0, int(config.get("preview_limit", 200)))
    except (TypeError, ValueError):
        limit = 200

    if not query or not tag:
        return

    note_ids_with_tag = mw.col.find_notes(f"tag:{tag}")
    if note_ids_with_tag:
        remove_tag_from_notes(mw.col, note_ids_with_tag, tag)

    card_ids = list(mw.col.find_cards(query, order="c.due asc"))
    if not card_ids:
        return
    note_ids = {mw.col.get_card(cid).nid for cid in card_ids[:limit]}
    if not note_ids:
        return
    added = tag_notes(mw.col, note_ids, tag)
    if added:
        tooltip("Added preview tag", period=2000)


def register_browser_hooks() -> None:
    if hasattr(gui_hooks, "browser_menus"):
        gui_hooks.browser_menus.append(_add_browser_menu)
    elif hasattr(gui_hooks, "browser_will_show"):
        gui_hooks.browser_will_show.append(_add_browser_menu)
    gui_hooks.browser_will_search.append(apply_card_limit)


def register_profile_hooks() -> None:
    gui_hooks.profile_did_open.append(lambda: auto_wrap_left_div_on_startup())
    gui_hooks.profile_did_open.append(lambda: auto_tag_preview_on_startup())


def _add_browser_menu(browser) -> None:
    action = QAction("Apply Cloze Pattern (Selected)", browser)
    action.triggered.connect(lambda: run_create_cloze_for_browser(browser))
    browser.form.menuEdit.addAction(action)

    advanced_menu = QMenu("Advanced", browser)
    for label, callback in BROWSER_ADVANCED_ACTIONS:
        action = QAction(label, browser)
        action.triggered.connect(lambda _checked=False, cb=callback: cb(browser))
        advanced_menu.addAction(action)
    browser.form.menuEdit.addMenu(advanced_menu)
