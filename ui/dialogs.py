from __future__ import annotations

from aqt.qt import *  # type: ignore[import]
from aqt.utils import getText, showInfo
from aqt import mw


def choose_deck_and_notetype() -> tuple[str | None, str | None]:
    """Return (deck_name, notetype_name) or (None, None) if cancelled."""
    if mw is None:
        showInfo("No Anki main window available.")
        return None, None

    deck_names = sorted(mw.col.decks.all_names_and_ids(), key=lambda d: d[0])
    note_names = sorted(mw.col.models.all_names_and_ids(), key=lambda n: n[0])

    deck_label = "Choose Deck"
    note_label = "Choose Notetype"

    deck_name = _choose_from_list(deck_label, [d[0] for d in deck_names])
    if deck_name is None:
        return None, None

    note_name = _choose_from_list(note_label, [n[0] for n in note_names])
    if note_name is None:
        return None, None

    return deck_name, note_name


def choose_field_from_notetype(
    notetype_name: str,
    prompt: str,
    allow_auto: bool = False,
) -> str | None:
    if mw is None:
        showInfo("No Anki main window available.")
        return None

    model = mw.col.models.by_name(notetype_name)
    if not model:
        showInfo(f"Notetype not found: {notetype_name}")
        return None

    fields = [f["name"] for f in model.get("flds", [])]
    items = fields[:]
    if allow_auto:
        items.insert(0, "Auto-detect")

    choice = _choose_from_list(prompt, items)
    if choice == "Auto-detect":
        return None
    return choice


def ask_field(prompt: str) -> str | None:
    text, ok = getText(prompt, parent=mw)
    if not ok:
        return None
    return text.strip() or None


def ask_yes_no(prompt: str) -> bool | None:
    box = QMessageBox(mw)
    box.setWindowTitle("Confirm")
    box.setText(prompt)
    box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    ret = box.exec()
    if ret == QMessageBox.StandardButton.Yes:
        return True
    if ret == QMessageBox.StandardButton.No:
        return False
    return None


def _choose_from_list(title: str, items: list[str]) -> str | None:
    if not items:
        showInfo(f"No options available for {title}.")
        return None

    dialog = QDialog(mw)
    dialog.setWindowTitle(title)

    layout = QVBoxLayout(dialog)
    list_widget = QListWidget(dialog)
    for item in items:
        list_widget.addItem(item)
    list_widget.setCurrentRow(0)
    layout.addWidget(list_widget)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    layout.addWidget(buttons)

    def _accept() -> None:
        dialog.accept()

    def _reject() -> None:
        dialog.reject()

    buttons.accepted.connect(_accept)
    buttons.rejected.connect(_reject)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    current = list_widget.currentItem()
    return current.text() if current else None
