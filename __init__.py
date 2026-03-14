from __future__ import annotations

from aqt import gui_hooks, mw, qconnect
from aqt.qt import QAction, QInputDialog
import re
from aqt.utils import askUser, showInfo, tooltip

from .operations.cloze import create_cloze
from .operations.br_cleanup import cleanup_br_runs
from .operations.bracket_check import check_square_brackets
from .operations.duplicates import suspend_duplicates
from .operations.field_wrap import wrap_field_in_left_div
from .operations.heisig_unsuspend import unsuspend_heisig_by_jp_lemmas
from .operations.heisig_links import populate_heisig_links_by_jp_lemmas
from .operations.no_html_check import tag_no_html
from .operations.japanese_char_check import tag_contains_japanese
from .operations.cloze_strip import strip_cloze_to_field


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


def _note_ids_for_notetype(notetype_name: str) -> list[int]:
    query = f'note:"{notetype_name}"'
    return list(mw.col.find_notes(query))


def _select_notetype_and_field() -> tuple[str, str] | None:
    notetype_name = _select_notetype_name()
    if not notetype_name:
        return None
    field_name = _select_field_name(notetype_name)
    if not field_name:
        return None
    return notetype_name, field_name


def _select_notetype_and_two_fields() -> tuple[str, str, str] | None:
    notetype_name = _select_notetype_name()
    if not notetype_name:
        return None
    source_field = _select_field_name(notetype_name)
    if not source_field:
        return None
    target_field = _select_field_name(notetype_name)
    if not target_field:
        return None
    return notetype_name, source_field, target_field


def _select_query(default_query: str) -> str | None:
    query, ok = QInputDialog.getText(mw, "Query", "Search Query:", text=default_query)
    if not ok:
        return None
    return str(query).strip() or default_query


def _select_dry_run(default: bool = False) -> bool | None:
    default_label = "true" if default else "false"
    label, ok = QInputDialog.getItem(
        mw,
        "Dry Run",
        "dry_run:",
        ["false", "true"],
        1 if default_label == "true" else 0,
        False,
    )
    if not ok or not label:
        return None
    return str(label).lower() == "true"


def _confirm_query_count(action_label: str, query: str, count: int) -> bool:
    return askUser(f"{action_label}\nQuery: {query}\nNotes: {count}")


def _maybe_backup() -> None:
    if not askUser("Create a backup before running this action?"):
        return
    try:
        mw.col.create_backup(
            backup_folder=mw.pm.backupFolder(),
            force=True,
            wait_for_completion=True,
        )
    except Exception as exc:
        showInfo(f"Backup failed: {exc}")


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

    _maybe_backup()
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
    _maybe_backup()
    result = suspend_duplicates(mw.col, query=query, dry_run=False)
    showInfo(f"suspend_duplicates finished: {result}")


action = QAction("Suspend Duplicates", mw)
qconnect(action.triggered, _run_suspend_duplicates)
mw.form.menuTools.addAction(action)


def _run_wrap_left_div_for_notetype() -> None:
    selection = _select_notetype_and_field()
    if not selection:
        return
    notetype_name, field_name = selection
    query = _select_query(f'note:"{notetype_name}"')
    if query is None:
        return
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for note type: {notetype_name}")
        return
    dry_run = _select_dry_run(False)
    if dry_run is None:
        return
    if not _confirm_query_count(
        f"Wrap left-div for '{field_name}'", query, len(note_ids)
    ):
        return
    if not dry_run:
        _maybe_backup()
    result = wrap_field_in_left_div(
        mw.col,
        note_ids,
        field_name=field_name,
        dry_run=dry_run,
    )
    showInfo(f"wrap_field_in_left_div finished: {result}")


action = QAction("Wrap Field Left Div (Note Type)", mw)
qconnect(action.triggered, _run_wrap_left_div_for_notetype)
mw.form.menuTools.addAction(action)


def _run_cleanup_br_runs_for_notetype() -> None:
    selection = _select_notetype_and_field()
    if not selection:
        return
    notetype_name, field_name = selection
    query = _select_query(f'note:"{notetype_name}"')
    if query is None:
        return
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for note type: {notetype_name}")
        return
    dry_run = _select_dry_run(False)
    if dry_run is None:
        return
    if not _confirm_query_count(
        f"Cleanup <br> runs for '{field_name}'", query, len(note_ids)
    ):
        return
    if not dry_run:
        _maybe_backup()
    result = cleanup_br_runs(
        mw.col,
        note_ids,
        field_name=field_name,
        dry_run=dry_run,
    )
    showInfo(f"cleanup_br_runs finished: {result}")


action = QAction("Cleanup <br> Runs (Note Type)", mw)
qconnect(action.triggered, _run_cleanup_br_runs_for_notetype)
mw.form.menuTools.addAction(action)


def _run_check_brackets_for_notetype() -> None:
    selection = _select_notetype_and_field()
    if not selection:
        return
    notetype_name, field_name = selection
    query = _select_query(f'note:"{notetype_name}"')
    if query is None:
        return
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for note type: {notetype_name}")
        return
    dry_run = _select_dry_run(False)
    if dry_run is None:
        return
    if not _confirm_query_count(
        f"Check square brackets in '{field_name}'", query, len(note_ids)
    ):
        return
    if not dry_run:
        _maybe_backup()
    result = check_square_brackets(
        mw.col,
        note_ids,
        field_name=field_name,
        dry_run=dry_run,
    )
    showInfo(f"check_square_brackets finished: {result}")


action = QAction("Check Square Brackets (Note Type)", mw)
qconnect(action.triggered, _run_check_brackets_for_notetype)
mw.form.menuTools.addAction(action)


def _run_no_html_check_for_notetype() -> None:
    selection = _select_notetype_and_field()
    if not selection:
        return
    notetype_name, field_name = selection
    query = _select_query(f'note:"{notetype_name}"')
    if query is None:
        return
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for note type: {notetype_name}")
        return
    dry_run = _select_dry_run(False)
    if dry_run is None:
        return
    if not _confirm_query_count(
        f"Tag no HTML in '{field_name}'", query, len(note_ids)
    ):
        return
    if not dry_run:
        _maybe_backup()
    result = tag_no_html(
        mw.col,
        note_ids,
        field_name=field_name,
        dry_run=dry_run,
    )
    showInfo(f"tag_no_html finished: {result}")


action = QAction("Tag No HTML (Note Type)", mw)
qconnect(action.triggered, _run_no_html_check_for_notetype)
mw.form.menuTools.addAction(action)


def _run_japanese_char_check_for_notetype() -> None:
    selection = _select_notetype_and_field()
    if not selection:
        return
    notetype_name, field_name = selection
    query = _select_query(f'note:"{notetype_name}"')
    if query is None:
        return
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for note type: {notetype_name}")
        return
    dry_run = _select_dry_run(False)
    if dry_run is None:
        return
    if not _confirm_query_count(
        f"Tag Japanese characters in '{field_name}'", query, len(note_ids)
    ):
        return
    if not dry_run:
        _maybe_backup()
    result = tag_contains_japanese(
        mw.col,
        note_ids,
        field_name=field_name,
        dry_run=dry_run,
    )
    showInfo(f"tag_contains_japanese finished: {result}")


action = QAction("Tag Japanese Characters (Note Type)", mw)
qconnect(action.triggered, _run_japanese_char_check_for_notetype)
mw.form.menuTools.addAction(action)


def _run_strip_cloze_for_notetype() -> None:
    selection = _select_notetype_and_two_fields()
    if not selection:
        return
    notetype_name, source_field, target_field = selection
    query = _select_query(f'note:"{notetype_name}"')
    if query is None:
        return
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for note type: {notetype_name}")
        return
    dry_run = _select_dry_run(False)
    if dry_run is None:
        return
    if not _confirm_query_count(
        f"Strip cloze from '{source_field}' to '{target_field}'", query, len(note_ids)
    ):
        return
    if not dry_run:
        _maybe_backup()
    result = strip_cloze_to_field(
        mw.col,
        note_ids,
        source_field=source_field,
        target_field=target_field,
        dry_run=dry_run,
    )
    showInfo(f"strip_cloze_to_field finished: {result}")


action = QAction("Strip Cloze to Field (Note Type)", mw)
qconnect(action.triggered, _run_strip_cloze_for_notetype)
mw.form.menuTools.addAction(action)


def _run_unsuspend_heisig_by_jp() -> None:
    if not askUser(
        "Unsuspend Heisig cards based on JP deck lemmas?\n"
        "JP deck: JP\n"
        "Heisig deck: Japanese Heisig::Deck in progress"
    ):
        return
    _maybe_backup()
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
        "JP fields: Lemma, Cloze"
    ):
        return
    _maybe_backup()
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


LIMIT_RE = re.compile(r"limit:(\d+)", re.IGNORECASE)


def _apply_card_limit(context) -> None:
    # Only apply to cards mode.
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

    # Order by lowest due (queue position) and limit results.
    card_ids = list(context.browser.col.find_cards(search, order="c.due asc"))
    context.ids = card_ids[:limit]
    context.search = search


gui_hooks.browser_will_search.append(_apply_card_limit)


def _auto_wrap_left_div_on_startup() -> None:
    notetype_name = "Moritz Language Reactor"
    query = f'note:"{notetype_name}"'
    note_ids = mw.col.find_notes(query)
    if not note_ids:
        return
    # Always run on both fields.
    wrap_field_in_left_div(
        mw.col,
        note_ids,
        field_name="Notes",
        dry_run=False,
    )
    wrap_field_in_left_div(
        mw.col,
        note_ids,
        field_name="Grammar",
        dry_run=False,
    )
    tooltip("applied left-div to Notes & Grammar")


gui_hooks.profile_did_open.append(lambda: _auto_wrap_left_div_on_startup())
