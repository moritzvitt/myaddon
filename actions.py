from __future__ import annotations

from aqt import mw
from aqt.utils import showInfo

from .config import RUN_STARTUP_GREEN_FLAG_REPLACEMENT_KEY, load_config
from .dialogs import _current_deck_name, select_run_options
from .operations.cloze import create_cloze
from .operations.cloze_hint_replace import (
    replace_cloze_hints,
    replace_cloze_hints_for_green_flagged_cards,
)
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


def run_startup_green_flag_replacement() -> dict[str, int] | None:
    if not bool(load_config().get(RUN_STARTUP_GREEN_FLAG_REPLACEMENT_KEY)):
        return None
    if mw is None or getattr(mw, "col", None) is None:
        return None
    return replace_cloze_hints_for_green_flagged_cards(mw.col, dry_run=False)


def _single_notetype_name_for_notes(note_ids: list[int]) -> str | None:
    names = {
        model.get("name")
        for nid in note_ids
        if (model := mw.col.get_note(nid).model())
    }
    names.discard(None)
    if len(names) == 1:
        return next(iter(names))
    return None


def _current_deck_notetype_name() -> str | None:
    deck_name = _current_deck_name()
    if not deck_name:
        return None
    note_ids = list(mw.col.find_notes(f'deck:"{deck_name}"'))
    if not note_ids:
        return None
    return _single_notetype_name_for_notes(note_ids)


def run_create_cloze_for_deck() -> None:
    current_deck = _current_deck_name()
    current_deck_notetype = _current_deck_notetype_name()

    options = select_run_options(
        title="Create Cloze (Query)",
        need_deck=True,
        need_notetype=True,
        field_labels=["Target Field", "Lemma Field", "Hint Field"],
        show_query=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_query="flag:3",
        default_dry_run=False,
        default_backup=False,
        default_deck=current_deck,
        default_notetype=current_deck_notetype or "Moritz Language Reactor",
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
    current_deck = _current_deck_name()
    current_deck_notetype = _current_deck_notetype_name()

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
        default_deck_filter=current_deck,
        default_dry_run=False,
        default_backup=False,
        default_overwrite=False,
        default_notetype=current_deck_notetype,
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
    current_deck = _current_deck_name()
    current_deck_notetype = _current_deck_notetype_name()

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
        default_deck_filter=current_deck,
        default_dry_run=False,
        default_backup=False,
        default_notetype=current_deck_notetype,
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


def _selected_notes_matching_notetype(
    note_ids: list[int], notetype_name: str
) -> list[int]:
    matched_ids: list[int] = []
    for nid in note_ids:
        note = mw.col.get_note(nid)
        model = note.model()
        if model and model.get("name") == notetype_name:
            matched_ids.append(nid)
    return matched_ids


def _selected_notetype_name(note_ids: list[int]) -> str | None:
    return _single_notetype_name_for_notes(note_ids)


def _selected_deck_name(note_ids: list[int]) -> str | None:
    deck_names = {
        mw.col.decks.name(mw.col.get_card(cid).did)
        for nid in note_ids
        for cid in mw.col.get_note(nid).card_ids()
    }
    deck_names.discard(None)
    if len(deck_names) == 1:
        return next(iter(deck_names))
    return None


def run_create_cloze_for_browser(browser) -> None:
    note_ids = _browser_selected_note_ids(browser)
    if not note_ids:
        showInfo("No notes selected.")
        return

    selected_notetype = _selected_notetype_name(note_ids)
    selected_deck = _selected_deck_name(note_ids)

    options = select_run_options(
        title="Apply Cloze Pattern (Selected)",
        need_deck=True,
        need_notetype=True,
        field_labels=["Target Field", "Lemma Field", "Hint Field"],
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
        default_deck=selected_deck,
        default_notetype=selected_notetype or "Moritz Language Reactor",
        default_fields=["Cloze", "Lemma", "Word Definition"],
        default_tag_filter="-tag:meta_single_lemma_generated",
    )
    if not options:
        return

    notetype_name = str(options["notetype"])
    deck_name = str(options["deck"])
    matched_ids = _selected_notes_matching_notetype(note_ids, notetype_name)
    if deck_name:
        matched_ids = [
            nid
            for nid in matched_ids
            if any(
                mw.col.decks.name(mw.col.get_card(cid).did) == deck_name
                for cid in mw.col.get_note(nid).card_ids()
            )
        ]
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


def run_replace_cloze_hints_for_browser(browser) -> None:
    note_ids = _browser_selected_note_ids(browser)
    if not note_ids:
        showInfo("No notes selected.")
        return

    selected_notetype = _selected_notetype_name(note_ids)

    options = select_run_options(
        title="Replace Cloze Hints (Selected)",
        need_notetype=True,
        field_labels=["Hint Field"],
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
        default_notetype=selected_notetype,
        default_fields=["Synonyms"],
    )
    if not options:
        return

    notetype_name = str(options["notetype"])
    matched_ids = _selected_notes_matching_notetype(note_ids, notetype_name)
    if not matched_ids:
        showInfo(
            f"No selected notes match note type '{notetype_name}'. "
            f"Selected: {len(note_ids)}"
        )
        return

    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        maybe_backup(force=True)

    result = replace_cloze_hints(
        mw.col,
        matched_ids,
        cloze_field="Cloze",
        hint_field=str(options["fields"][0]),
        dry_run=dry_run,
    )
    if len(matched_ids) != len(note_ids):
        showInfo(
            f"Replaced hints on {len(matched_ids)} of {len(note_ids)} selected notes "
            f"(note type '{notetype_name}').\n"
            f"replace_cloze_hints finished: {result}"
        )
        return
    showInfo(f"replace_cloze_hints finished: {result}")


TOOLS_MENU_ACTIONS: list[tuple[str, object]] = [
    ("Create Cloze (Query)", run_create_cloze_for_deck),
    ("Replace Cloze Hints (Note Type)", run_replace_cloze_hints_for_notetype),
    ("Strip Cloze to Field (Note Type)", run_strip_cloze_for_notetype),
]
