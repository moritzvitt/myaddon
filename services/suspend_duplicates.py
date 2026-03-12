from __future__ import annotations

from aqt import mw
from aqt.utils import showInfo

from anki import query as anki_query
from anki import notes as anki_notes
from services import tag_rules
from ui.dialogs import choose_deck_and_notetype, choose_field_from_notetype


DEFAULT_QUERY = "deck:JP -tag:meta::retired -flag:5"


def suspend_duplicates() -> None:
    deck_name, notetype_name = choose_deck_and_notetype()
    if not deck_name or not notetype_name:
        return

    word_field = choose_field_from_notetype(
        notetype_name,
        "Which field contains the Word you are learning?",
        allow_auto=False,
    )
    if word_field is None:
        return

    notetype_fields = anki_notes.get_note_type_field_names(notetype_name)
    lemma_field = None
    if "Lemma" in notetype_fields:
        lemma_field = "Lemma"
    elif "lemma" in notetype_fields:
        lemma_field = "lemma"
    elif notetype_fields:
        lemma_field = notetype_fields[0]

    excluded = " ".join([f'-tag:\"{t}\"' for t in tag_rules.excluded_tags()])
    query = f"{DEFAULT_QUERY} deck:\"{deck_name}\" note:\"{notetype_name}\" {excluded}".strip()
    note_ids = anki_query.find_notes_by_query(query)

    if not note_ids:
        showInfo("No notes found for selection.")
        return

    if mw is None:
        showInfo("No Anki main window available.")
        return

    groups: dict[str, list[int]] = {}
    for note_id in note_ids:
        note = anki_notes.get_note(note_id)
        if note is None:
            continue
        key_field = lemma_field or word_field
        key_value = (note[key_field] or "").strip() if key_field in note else ""
        if not key_value:
            continue
        groups.setdefault(key_value, []).append(note_id)

    unsuspended_notes = 0
    skipped_learning = 0
    total_groups = 0

    for group_note_ids in groups.values():
        if len(group_note_ids) < 2:
            continue
        total_groups += 1

        card_ids = []
        for note_id in group_note_ids:
            note = anki_notes.get_note(note_id)
            if note is None:
                continue
            card_ids.extend(note.card_ids())

        if not card_ids:
            continue

        cards = [mw.col.get_card(cid) for cid in card_ids]
        if any(card.queue in (1, 2, 3) for card in cards):
            skipped_learning += 1
            continue

        best_note_id = None
        best_key = None
        for note_id in group_note_ids:
            note = anki_notes.get_note(note_id)
            if note is None:
                continue
            note_card_ids = note.card_ids()
            note_cards = [mw.col.get_card(cid) for cid in note_card_ids]
            for card in note_cards:
                if card.type == 0 or card.queue in (0, -1):
                    key = (card.due, card.id)
                    if best_key is None or key < best_key:
                        best_key = key
                        best_note_id = note_id

        if best_note_id is None:
            continue

        best_note = anki_notes.get_note(best_note_id)
        if best_note is None:
            continue

        mw.col.sched.unsuspend_cards(best_note.card_ids())
        unsuspended_notes += 1

    showInfo(
        "Suspend Duplicates finished.\n"
        f"Word field: {word_field}\n"
        f"Lemma field: {lemma_field or word_field}\n"
        f"Groups scanned: {total_groups}\n"
        f"Unsuspended notes: {unsuspended_notes}\n"
        f"Skipped (already learning): {skipped_learning}"
    )
