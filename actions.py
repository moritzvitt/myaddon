from __future__ import annotations

from aqt import mw
from aqt.utils import askUser, showInfo

from .dialogs import open_config_dialog, select_run_options
from .operations.cloze import create_cloze
from .operations.cloze_hint_replace import replace_cloze_hints
from .operations.cloze_strip import strip_cloze_to_field
from .operations.hidden.br_cleanup import cleanup_br_runs
from .operations.hidden.bracket_check import check_square_brackets
from .operations.hidden.card_type_check import classify_card_type
from .operations.hidden.field_overwrite import overwrite_field_from_field
from .operations.hidden.field_wrap import wrap_field_in_left_div
from .operations.hidden.heisig_links import populate_heisig_links_by_jp_lemmas
from .operations.hidden.heisig_unsuspend import unsuspend_heisig_by_jp_lemmas
from .operations.hidden.japanese_char_check import tag_contains_japanese
from .operations.hidden.no_html_check import tag_no_html


def maybe_backup(force: bool | None = None) -> None:
    if force is None:
        if not askUser("Create a backup before running this action?"):
            return
    elif not force:
        return
    try:
        mw.col.create_backup(
            backup_folder=mw.pm.backupFolder(),
            force=True,
            wait_for_completion=True,
        )
    except Exception as exc:
        showInfo(f"Backup failed: {exc}")


def run_create_cloze_for_deck() -> None:
    options = select_run_options(
        title="Create Cloze (Query)",
        need_deck=True,
        need_notetype=True,
        field_labels=["Target Field", "Lemma Field", "Hint Field"],
        show_query=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
        default_notetype="Moritz Language Reactor",
        default_fields=["Cloze", "Lemma", "Word Definition"],
        default_tag_filter="-tag:meta_single_lemma_generated",
        use_deck_combo_in_query=True,
    )
    if not options:
        return

    target_field = str(options["fields"][0])
    lemma_field = str(options["fields"][1])
    hint_field = str(options["fields"][2])
    query = str(options["query"] or "")
    if "-tag:meta_single_lemma_generated" not in query:
        query = f"{query} -tag:meta_single_lemma_generated"
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        maybe_backup(force=True)
    result = create_cloze(
        mw.col,
        note_ids,
        target_field=target_field,
        lemma_field=lemma_field,
        hint_field=hint_field,
        dry_run=dry_run,
    )
    showInfo(f"create_cloze finished: {result}")


def run_open_config() -> None:
    open_config_dialog()


def _run_notetype_field_action(
    *,
    title: str,
    field_labels: list[str],
    runner,
    result_label: str,
    default_query_template: str | None = None,
    default_fields: list[str] | None = None,
    show_overwrite: bool = False,
    default_overwrite: bool = False,
) -> None:
    options = select_run_options(
        title=title,
        need_notetype=True,
        field_labels=field_labels,
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        show_overwrite=show_overwrite,
        default_query_template=default_query_template,
        default_dry_run=False,
        default_backup=False,
        default_overwrite=default_overwrite,
        default_fields=default_fields,
    )
    if not options:
        return

    query = str(options["query"] or "")
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        maybe_backup(force=True)

    result = runner(note_ids, options, dry_run)
    showInfo(f"{result_label} finished: {result}")


def run_wrap_left_div_for_notetype() -> None:
    _run_notetype_field_action(
        title="Wrap Field Left Div (Note Type)",
        field_labels=["Field"],
        result_label="wrap_field_in_left_div",
        runner=lambda note_ids, options, dry_run: wrap_field_in_left_div(
            mw.col,
            note_ids,
            field_name=str(options["fields"][0]),
            dry_run=dry_run,
        ),
    )


def run_cleanup_br_runs_for_notetype() -> None:
    _run_notetype_field_action(
        title="Cleanup <br> Runs (Note Type)",
        field_labels=["Field"],
        result_label="cleanup_br_runs",
        runner=lambda note_ids, options, dry_run: cleanup_br_runs(
            mw.col,
            note_ids,
            field_name=str(options["fields"][0]),
            dry_run=dry_run,
        ),
    )


def run_check_brackets_for_notetype() -> None:
    _run_notetype_field_action(
        title="Check Square Brackets (Note Type)",
        field_labels=["Field"],
        result_label="check_square_brackets",
        runner=lambda note_ids, options, dry_run: check_square_brackets(
            mw.col,
            note_ids,
            field_name=str(options["fields"][0]),
            dry_run=dry_run,
        ),
    )


def run_no_html_check_for_notetype() -> None:
    _run_notetype_field_action(
        title="Tag No HTML (Note Type)",
        field_labels=["Field"],
        result_label="tag_no_html",
        runner=lambda note_ids, options, dry_run: tag_no_html(
            mw.col,
            note_ids,
            field_name=str(options["fields"][0]),
            dry_run=dry_run,
        ),
    )


def run_japanese_char_check_for_notetype() -> None:
    _run_notetype_field_action(
        title="Tag Japanese Characters (Note Type)",
        field_labels=["Field"],
        result_label="tag_contains_japanese",
        runner=lambda note_ids, options, dry_run: tag_contains_japanese(
            mw.col,
            note_ids,
            field_name=str(options["fields"][0]),
            dry_run=dry_run,
        ),
    )


def run_card_type_check_for_notetype() -> None:
    _run_notetype_field_action(
        title="Tag Word vs Sentence Cards (Note Type)",
        field_labels=["Cloze Field"],
        result_label="classify_card_type",
        default_fields=["Cloze"],
        runner=lambda note_ids, options, dry_run: classify_card_type(
            mw.col,
            note_ids,
            cloze_field=str(options["fields"][0]),
            dry_run=dry_run,
        ),
    )


def run_strip_cloze_for_notetype() -> None:
    _run_notetype_field_action(
        title="Strip Cloze to Field (Note Type)",
        field_labels=["Source Field", "Target Field"],
        result_label="strip_cloze_to_field",
        show_overwrite=True,
        default_overwrite=False,
        runner=lambda note_ids, options, dry_run: strip_cloze_to_field(
            mw.col,
            note_ids,
            source_field=str(options["fields"][0]),
            target_field=str(options["fields"][1]),
            overwrite_target=bool(options.get("overwrite_target")),
            dry_run=dry_run,
        ),
    )


def run_replace_cloze_hints_for_notetype() -> None:
    _run_notetype_field_action(
        title="Replace Cloze Hints (Note Type)",
        field_labels=["Hint Field"],
        result_label="replace_cloze_hints",
        default_query_template='note:"{notetype}" deck:migaku tag:meta::multi_lemma',
        runner=lambda note_ids, options, dry_run: replace_cloze_hints(
            mw.col,
            note_ids,
            cloze_field="Cloze",
            hint_field=str(options["fields"][0]),
            dry_run=dry_run,
        ),
    )


def run_unsuspend_heisig_by_jp() -> None:
    if not askUser(
        "Unsuspend Heisig cards based on JP deck lemmas?\n"
        "JP deck: JP\n"
        "Heisig deck: Japanese Heisig::Deck in progress"
    ):
        return
    maybe_backup()
    result = unsuspend_heisig_by_jp_lemmas(mw.col, dry_run=False)
    showInfo(f"unsuspend_heisig_by_jp_lemmas finished: {result}")


def run_heisig_links_by_jp() -> None:
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
    maybe_backup()
    result = populate_heisig_links_by_jp_lemmas(mw.col, dry_run=False)
    showInfo(f"populate_heisig_links_by_jp_lemmas finished: {result}")


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


def run_create_cloze_for_browser(browser) -> None:
    note_ids = _browser_selected_note_ids(browser)
    if not note_ids:
        showInfo("No notes selected.")
        return
    options = select_run_options(
        title="Apply Cloze Pattern (Selected)",
        need_deck=True,
        need_notetype=True,
        field_labels=["Target Field", "Lemma Field", "Hint Field"],
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
        default_notetype="Moritz Language Reactor",
        default_fields=["Cloze", "Lemma", "Word Definition"],
        default_tag_filter="-tag:meta_single_lemma_generated",
    )
    if not options:
        return
    notetype_name = str(options["notetype"])
    deck_name = str(options["deck"])
    target_field = str(options["fields"][0])
    lemma_field = str(options["fields"][1])
    hint_field = str(options["fields"][2])
    matched_ids: list[int] = []
    for nid in note_ids:
        note = mw.col.get_note(nid)
        model = note.model()
        if model and model.get("name") == notetype_name:
            if deck_name:
                card_ids = note.card_ids()
                if any(
                    mw.col.decks.name(mw.col.get_card(cid).did) == deck_name
                    for cid in card_ids
                ):
                    matched_ids.append(nid)
            else:
                matched_ids.append(nid)
    if not matched_ids:
        showInfo(
            f"No selected notes match note type '{notetype_name}'"
            f"{f' in deck {deck_name!r}' if deck_name else ''}. "
            f"Selected: {len(note_ids)}"
        )
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        maybe_backup(force=True)
    result = create_cloze(
        mw.col,
        matched_ids,
        target_field=target_field,
        lemma_field=lemma_field,
        hint_field=hint_field,
        dry_run=dry_run,
    )
    if len(matched_ids) != len(note_ids):
        showInfo(
            f"Applied to {len(matched_ids)} of {len(note_ids)} selected notes "
            f"(note type '{notetype_name}'"
            f"{f', deck {deck_name!r}' if deck_name else ''}).\n"
            f"create_cloze finished: {result}"
        )
        return
    showInfo(f"create_cloze finished: {result}")


def run_overwrite_field_for_browser(browser) -> None:
    note_ids = _browser_selected_note_ids(browser)
    if not note_ids:
        showInfo("No notes selected.")
        return
    options = select_run_options(
        title="Overwrite Field From Field (Selected)",
        need_notetype=True,
        field_labels=["Source Field", "Target Field"],
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
    )
    if not options:
        return
    notetype_name = str(options["notetype"])
    source_field = str(options["fields"][0])
    target_field = str(options["fields"][1])
    matched_ids: list[int] = []
    for nid in note_ids:
        note = mw.col.get_note(nid)
        model = note.model()
        if model and model.get("name") == notetype_name:
            matched_ids.append(nid)
    if not matched_ids:
        showInfo(
            f"No selected notes match note type '{notetype_name}'. "
            f"Selected: {len(note_ids)}"
        )
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        maybe_backup(force=True)
    result = overwrite_field_from_field(
        mw.col,
        matched_ids,
        source_field=source_field,
        target_field=target_field,
        dry_run=dry_run,
    )
    if len(matched_ids) != len(note_ids):
        showInfo(
            f"Applied to {len(matched_ids)} of {len(note_ids)} selected notes "
            f"(note type '{notetype_name}').\n"
            f"overwrite_field_from_field finished: {result}"
        )
        return
    showInfo(f"overwrite_field_from_field finished: {result}")


def add_browser_menu(browser) -> None:
    action = QAction("Apply Cloze Pattern (Selected)", browser)
    qconnect(action.triggered, lambda: run_create_cloze_for_browser(browser))
    browser.form.menuEdit.addAction(action)
    

MAIN_TOOLS_MENU_ACTIONS: list[tuple[str, object]] = [
    ("Create Cloze (Query)", run_create_cloze_for_deck),
    ("Replace Cloze Hints (Note Type)", run_replace_cloze_hints_for_notetype),
    ("Strip Cloze to Field (Note Type)", run_strip_cloze_for_notetype),
    ("Misc Formatting Configuration", run_open_config),
]

ADVANCED_TOOLS_MENU_ACTIONS: list[tuple[str, object]] = [
    ("Wrap Field Left Div (Note Type)", run_wrap_left_div_for_notetype),
    ("Cleanup <br> Runs (Note Type)", run_cleanup_br_runs_for_notetype),
    ("Unsuspend Heisig by JP Lemmas", run_unsuspend_heisig_by_jp),
    ("Populate Heisig Links from JP", run_heisig_links_by_jp),
]

DIAGNOSTICS_TOOLS_MENU_ACTIONS: list[tuple[str, object]] = [
    ("Check Square Brackets (Note Type)", run_check_brackets_for_notetype),
    ("Tag No HTML (Note Type)", run_no_html_check_for_notetype),
    ("Tag Japanese Characters (Note Type)", run_japanese_char_check_for_notetype),
    ("Tag Word vs Sentence Cards (Note Type)", run_card_type_check_for_notetype),
]

BROWSER_ADVANCED_ACTIONS: list[tuple[str, object]] = [
    ("Overwrite Field From Field (Selected)", run_overwrite_field_for_browser),
]
