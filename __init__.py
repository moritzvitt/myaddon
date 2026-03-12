from __future__ import annotations

from aqt import gui_hooks, mw, qconnect
from aqt.qt import QAction, QInputDialog
from aqt.utils import askUser, showInfo

from .operations.cloze import create_cloze
from .operations.duplicates import suspend_duplicates


def _select_deck_name() -> str | None:
    decks = mw.col.decks.all_names_and_ids()
    if not decks:
        showInfo("No decks found.")
        return None
    names = sorted(d.name for d in decks)
    name, ok = QInputDialog.getItem(mw, "Select Deck", "Deck:", names, 0, False)
    if not ok or not name:
        return None
    return str(name)


def _run_create_cloze_for_deck() -> None:
    deck_name = _select_deck_name()
    if not deck_name:
        return

    query = f'deck:"{deck_name}"'
    note_ids = mw.col.find_notes(query)
    if not note_ids:
        showInfo(f"No notes found in deck: {deck_name}")
        return

    if not askUser(f"Run cloze update on {len(note_ids)} notes in '{deck_name}'?"):
        return

    result = create_cloze(mw.col, note_ids, dry_run=False)
    showInfo(f"create_cloze finished: {result}")


action = QAction("Create Cloze (Deck)", mw)
qconnect(action.triggered, _run_create_cloze_for_deck)
mw.form.menuTools.addAction(action)


def _run_suspend_duplicates() -> None:
    deck_name = _select_deck_name()
    if not deck_name:
        return
    exclude_suspended_flags = " ".join(
        f"-(is:suspended flag:{flag})" for flag in (1, 2, 4, 5, 6, 7)
    )
    deck_query = f'deck:"{deck_name}" or deck:"{deck_name}::*"'
    query = f"({deck_query}) -tag:meta::retired {exclude_suspended_flags}"
    note_count = len(mw.col.find_notes(query))
    card_count = len(mw.col.find_cards(query))
    showInfo(
        "Duplicate query:\n"
        f"{query}\n"
        f"Notes: {note_count}\n"
        f"Cards: {card_count}"
    )
    if not askUser(f"Run duplicate suspension on {query}?"):
        return
    result = suspend_duplicates(mw.col, query=query, dry_run=False)
    showInfo(f"suspend_duplicates finished: {result}")


action = QAction("Suspend Duplicates", mw)
qconnect(action.triggered, _run_suspend_duplicates)
mw.form.menuTools.addAction(action)


def _browser_selected_note_ids(browser) -> list[int]:
    if hasattr(browser, "selected_notes"):
        return list(browser.selected_notes())
    if hasattr(browser, "selectedNotes"):
        return list(browser.selectedNotes())
    if hasattr(browser, "selected_cards"):
        card_ids = browser.selected_cards()
        return list({mw.col.get_card(cid).note_id for cid in card_ids})
    if hasattr(browser, "selectedCards"):
        card_ids = browser.selectedCards()
        return list({mw.col.get_card(cid).note_id for cid in card_ids})
    return []


def _run_create_cloze_for_browser(browser) -> None:
    note_ids = _browser_selected_note_ids(browser)
    if not note_ids:
        showInfo("No notes selected.")
        return
    if not askUser(f"Apply cloze pattern to {len(note_ids)} selected notes?"):
        return
    result = create_cloze(mw.col, note_ids, dry_run=False)
    showInfo(f"create_cloze finished: {result}")


def _add_browser_menu(browser) -> None:
    action = QAction("Apply Cloze Pattern (Selected)", browser)
    qconnect(action.triggered, lambda: _run_create_cloze_for_browser(browser))
    browser.form.menuEdit.addAction(action)


if hasattr(gui_hooks, "browser_menus"):
    gui_hooks.browser_menus.append(_add_browser_menu)
elif hasattr(gui_hooks, "browser_will_show"):
    gui_hooks.browser_will_show.append(_add_browser_menu)
