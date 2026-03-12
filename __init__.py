from __future__ import annotations

from aqt import gui_hooks, mw, qconnect
from aqt.qt import QAction, QInputDialog
from aqt.utils import askUser, showInfo

from .operations.cloze import create_cloze
from .operations.br_cleanup import cleanup_br_runs
from .operations.duplicates import suspend_duplicates
from .operations.field_wrap import wrap_field_in_left_div
from .operations.heisig_unsuspend import unsuspend_heisig_by_jp_lemmas
from .operations.heisig_links import populate_heisig_links_by_jp_lemmas


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


def _select_notetype_name() -> str | None:
    models = mw.col.models
    if hasattr(models, "all_names_and_ids"):
        names = sorted(m.name for m in models.all_names_and_ids())
    else:
        names = sorted(m["name"] for m in models.all())
    if not names:
        showInfo("No note types found.")
        return None
    name, ok = QInputDialog.getItem(mw, "Select Note Type", "Note Type:", names, 0, False)
    if not ok or not name:
        return None
    return str(name)


def _select_field_name(notetype_name: str) -> str | None:
    model = mw.col.models.by_name(notetype_name)
    if not model:
        showInfo(f"Note type not found: {notetype_name}")
        return None
    fields = [f["name"] for f in model.get("flds", [])]
    if not fields:
        showInfo(f"No fields found in note type: {notetype_name}")
        return None
    name, ok = QInputDialog.getItem(mw, "Select Field", "Field:", fields, 0, False)
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


def _run_wrap_left_div_for_notetype() -> None:
    notetype_name = _select_notetype_name()
    if not notetype_name:
        return
    field_name = _select_field_name(notetype_name)
    if not field_name:
        return
    query = f'note:"{notetype_name}"'
    note_ids = mw.col.find_notes(query)
    if not note_ids:
        showInfo(f"No notes found for note type: {notetype_name}")
        return
    if not askUser(
        f"Wrap field '{field_name}' with <div style=\"text-align:left;\"> "
        f"for {len(note_ids)} notes of '{notetype_name}'?"
    ):
        return
    result = wrap_field_in_left_div(
        mw.col,
        note_ids,
        field_name=field_name,
        dry_run=False,
    )
    showInfo(f"wrap_field_in_left_div finished: {result}")


action = QAction("Wrap Field Left Div (Note Type)", mw)
qconnect(action.triggered, _run_wrap_left_div_for_notetype)
mw.form.menuTools.addAction(action)


def _run_cleanup_br_runs_for_notetype() -> None:
    notetype_name = _select_notetype_name()
    if not notetype_name:
        return
    field_name = _select_field_name(notetype_name)
    if not field_name:
        return
    query = f'note:"{notetype_name}"'
    note_ids = mw.col.find_notes(query)
    if not note_ids:
        showInfo(f"No notes found for note type: {notetype_name}")
        return
    if not askUser(
        f"Reduce <br> runs to 3 in field '{field_name}' "
        f"for {len(note_ids)} notes of '{notetype_name}'?"
    ):
        return
    result = cleanup_br_runs(
        mw.col,
        note_ids,
        field_name=field_name,
        dry_run=False,
    )
    showInfo(f"cleanup_br_runs finished: {result}")


action = QAction("Cleanup <br> Runs (Note Type)", mw)
qconnect(action.triggered, _run_cleanup_br_runs_for_notetype)
mw.form.menuTools.addAction(action)


def _run_unsuspend_heisig_by_jp() -> None:
    if not askUser(
        "Unsuspend Heisig cards based on JP deck lemmas?\n"
        "JP deck: JP\n"
        "Heisig deck: Japanese Heisig::Deck in progress"
    ):
        return
    result = unsuspend_heisig_by_jp_lemmas(mw.col, dry_run=False)
    showInfo(f"unsuspend_heisig_by_jp_lemmas finished: {result}")


action = QAction("Unsuspend Heisig by JP Lemmas", mw)
qconnect(action.triggered, _run_unsuspend_heisig_by_jp)
mw.form.menuTools.addAction(action)


def _run_heisig_links_by_jp() -> None:
    if not askUser(
        "Populate Heisig Link field from JP deck?\n"
        "Order: lower due first (so you see related JP cards sooner).\n"
        "JP deck: JP\n"
        "Heisig deck: Japanese Heisig::Deck in progress\n"
        "Heisig note type: HeisigKanjiJapanese\n"
        "Heisig field: Link\n"
        "JP fields: Lemma, Subtitle"
    ):
        return
    result = populate_heisig_links_by_jp_lemmas(mw.col, dry_run=False)
    showInfo(f"populate_heisig_links_by_jp_lemmas finished: {result}")


action = QAction("Populate Heisig Links from JP", mw)
qconnect(action.triggered, _run_heisig_links_by_jp)
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
