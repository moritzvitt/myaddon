from __future__ import annotations

from aqt import mw
from aqt.utils import showInfo

from .dialogs import select_run_options
from .operations.cloze import create_cloze
from .operations.cloze_hint_replace import replace_cloze_hints
from .operations.cloze_strip import strip_cloze_to_field


def maybe_backup(force: bool | None = None) -> None:
    if force is None or not force:
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
        target_field=str(options["fields"][0]),
        lemma_field=str(options["fields"][1]),
        hint_field=str(options["fields"][2]),
        dry_run=dry_run,
    )
    showInfo(f"create_cloze finished: {result}")


def run_strip_cloze_for_notetype() -> None:
    options = select_run_options(
        title="Strip Cloze to Field (Note Type)",
        need_notetype=True,
        field_labels=["Source Field", "Target Field"],
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        show_overwrite=True,
        default_dry_run=False,
        default_backup=False,
        default_overwrite=False,
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

    result = strip_cloze_to_field(
        mw.col,
        note_ids,
        source_field=str(options["fields"][0]),
        target_field=str(options["fields"][1]),
        overwrite_target=bool(options.get("overwrite_target")),
        dry_run=dry_run,
    )
    showInfo(f"strip_cloze_to_field finished: {result}")


def run_replace_cloze_hints_for_notetype() -> None:
    options = select_run_options(
        title="Replace Cloze Hints (Note Type)",
        need_notetype=True,
        field_labels=["Hint Field"],
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_query_template='note:"{notetype}"',
        default_dry_run=False,
        default_backup=False,
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

    result = replace_cloze_hints(
        mw.col,
        note_ids,
        cloze_field="Cloze",
        hint_field=str(options["fields"][0]),
        dry_run=dry_run,
    )
    showInfo(f"replace_cloze_hints finished: {result}")


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
        target_field=str(options["fields"][0]),
        lemma_field=str(options["fields"][1]),
        hint_field=str(options["fields"][2]),
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


TOOLS_MENU_ACTIONS: list[tuple[str, object]] = [
    ("Create Cloze (Query)", run_create_cloze_for_deck),
    ("Replace Cloze Hints (Note Type)", run_replace_cloze_hints_for_notetype),
    ("Strip Cloze to Field (Note Type)", run_strip_cloze_for_notetype),
]
