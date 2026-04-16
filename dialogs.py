from __future__ import annotations

import re

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QToolButton,
    QWidget,
)
from aqt.utils import showInfo

from .config import (
    GREEN_FLAG_SYNONYM_MODE_KEY,
    RUN_STARTUP_GREEN_FLAG_REPLACEMENT_KEY,
    SYNONYM_MODE_LABELS,
    load_config,
    save_config,
)
from . import shared_styling


FIELD_TOOLTIPS = {
    "Target Field": "This field will be written by the action. Choose the field where you want the final cloze or plain-text result to end up.",
    "Lemma Field": "This field provides the lemma or base form used for matching against the sentence content.",
    "Hint Field": "This field provides the hint text that will appear inside the cloze, such as `Word Definition` or `Synonyms`.",
    "Source Field": "This field is read as the input source when stripping cloze markup into another field.",
}

CONTROL_TOOLTIPS = {
    "Deck": "Limits the action to notes whose cards belong to this deck.",
    "Note Type": "Chooses which note type the selected fields should come from.",
    "Query": "Search string used to find notes for this batch action. It starts from the dialog defaults until you edit it.",
    "Deck Filter": "Extra deck restriction appended to the generated query.",
    "Tag Filter": "Extra tag terms appended to the generated query, such as exclusions for already-processed notes.",
    "Green flag synonym mode": "Controls whether a green-flagged card uses the first synonym, first two synonyms, or all synonyms as hint text.",
    "Run startup green-flag replacement": "Runs the green-flag synonym replacement automatically when Anki starts, then clears the processed green flags.",
}

OPTION_TOOLTIPS = {
    "Dry run": "Shows what would be changed without writing anything to your notes.",
    "Create backup before running": "Creates an Anki backup before the action writes any note changes.",
    "Overwrite target field": "Allows existing content in the target field to be replaced.",
}

MENU_INFO_TEXTS = {
    "Create Cloze (Query)": "Use this menu when you want to batch-create clozes from a search query. The query can target a current deck, green-flagged cards, or a filtered backlog, while the field selectors decide where the addon reads lemmas and writes the finished cloze.",
    "Strip Cloze to Field (Note Type)": "Use this when you want a plain-text version of cloze content in another field. It reads existing cloze text from the source field and writes stripped output into the target field.",
    "Replace Cloze Hints (Note Type)": "Use this to refresh hint text in bulk for all notes matching a query. Pick the field that should become the new cloze hint, such as `Word Definition` or `Synonyms`.",
    "Replace Cloze Hints (Selected)": "Use this for a hand-picked set of notes in the Browser. It only touches the notes you selected, which makes it a safer way to test synonym-based hint replacement before running a wider batch.",
    "Apply Cloze Pattern (Selected)": "This looks for the lemma from the configured lemma field inside the sentence in the target field and wraps the matched word with Anki's cloze structure. The matched lemma becomes the hidden word, and the configured hint field, such as `Word Definition`, becomes the cloze hint.",
    "Settings": "This menu controls addon-wide behavior rather than one batch run. You can define how green-flag synonym hints behave and whether flagged cards should be processed automatically when Anki starts.",
}


def _tooltip_for_title(title: str) -> str | None:
    return {
        "Create Cloze (Query)": "Batch-process notes from a search query. This is the fastest way to work through a current deck or green-flagged backlog.",
        "Strip Cloze to Field (Note Type)": "Create a plain-text companion field from existing clozes. Useful for exports, comparisons, or fallback study views.",
        "Replace Cloze Hints (Note Type)": "Refresh hint text in bulk when your support field has improved and you want clozes to reflect it.",
        "Replace Cloze Hints (Selected)": "Replace cloze hints only on the notes you selected in the Browser. Useful for switching a small hand-picked set over to synonym-based hints.",
        "Apply Cloze Pattern (Selected)": "Run cloze generation only on the notes you picked in the Browser. Useful for careful spot-fixes before rolling changes out more widely.",
        "Settings": "Configure optional Cloze Formatting behavior. This is where the green-flag synonym workflow becomes predictable and repeatable.",
    }.get(title)


def _deck_names() -> list[str]:
    decks = mw.col.decks.all_names_and_ids()
    return sorted(d.name for d in decks)


def _current_deck_name() -> str | None:
    current = mw.col.decks.current()
    if hasattr(current, "name"):
        return str(current.name)
    if isinstance(current, dict):
        name = current.get("name")
        return str(name) if name else None
    return None


def _notetype_names() -> list[str]:
    models = mw.col.models
    if hasattr(models, "all_names_and_ids"):
        return sorted(m.name for m in models.all_names_and_ids())
    return sorted(m["name"] for m in models.all())


def _field_names_for_notetype(notetype_name: str) -> list[str]:
    model = mw.col.models.by_name(notetype_name)
    if not model:
        return []
    return [f["name"] for f in model.get("flds", [])]


def _query_term_for_tag_filter(tag: str) -> str:
    cleaned = tag.strip()
    if not cleaned:
        return ""
    if ":" in cleaned:
        return cleaned
    if cleaned.startswith("-"):
        return f"-tag:{cleaned[1:]}"
    return f"tag:{cleaned}"


def _show_info_popup(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.information(parent, title, text)


def _make_menu_info_row(parent: QWidget, title: str) -> QWidget | None:
    info_text = MENU_INFO_TEXTS.get(title)
    if not info_text:
        return None

    container = QWidget(parent)
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    button = QToolButton(container)
    button.setText("What is this useful for?")
    button.clicked.connect(
        lambda _checked=False, popup_title=title, popup_text=info_text: _show_info_popup(
            parent, popup_title, popup_text
        )
    )
    layout.addWidget(button)
    layout.addStretch(1)
    return container


class RunOptionsDialog(QDialog):
    def __init__(
        self,
        *,
        title: str,
        deck_names: list[str] | None = None,
        notetype_names: list[str] | None = None,
        field_labels: list[str] | None = None,
        show_query: bool = False,
        default_query: str = "",
        default_query_template: str | None = None,
        show_deck_filter: bool = False,
        show_tag_filter: bool = False,
        default_deck_filter: str | None = None,
        default_tag_filter: str | None = None,
        default_deck: str | None = None,
        use_deck_combo_in_query: bool = False,
        show_dry_run: bool = False,
        default_dry_run: bool = False,
        show_backup: bool = False,
        default_backup: bool = False,
        show_overwrite: bool = False,
        default_overwrite: bool = False,
        default_notetype: str | None = None,
        default_fields: list[str] | None = None,
    ) -> None:
        super().__init__(mw)
        self.setWindowTitle(title)
        title_tooltip = _tooltip_for_title(title)
        if title_tooltip:
            self.setToolTip(title_tooltip)
        self._default_query = default_query
        self._default_query_template = default_query_template
        self._query_dirty = False
        self._default_fields = default_fields or []
        self._use_deck_combo_in_query = use_deck_combo_in_query

        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        info_row = _make_menu_info_row(self, title)
        if info_row is not None:
            layout.addRow("", info_row)

        self.deck_combo: QComboBox | None = None
        if deck_names is not None:
            self.deck_combo = QComboBox()
            self.deck_combo.addItems(deck_names)
            self.deck_combo.setToolTip(CONTROL_TOOLTIPS["Deck"])
            if default_deck and default_deck in deck_names:
                self.deck_combo.setCurrentIndex(deck_names.index(default_deck))
            layout.addRow("Deck:", self.deck_combo)

        self.notetype_combo: QComboBox | None = None
        if notetype_names is not None:
            self.notetype_combo = QComboBox()
            self.notetype_combo.addItems(notetype_names)
            self.notetype_combo.setToolTip(CONTROL_TOOLTIPS["Note Type"])
            if default_notetype and default_notetype in notetype_names:
                self.notetype_combo.setCurrentIndex(notetype_names.index(default_notetype))
            layout.addRow("Note Type:", self.notetype_combo)

        self.field_combos: list[QComboBox] = []
        if field_labels:
            for label in field_labels:
                combo = QComboBox()
                combo.setToolTip(
                    FIELD_TOOLTIPS.get(
                        label,
                        f"Choose which note field to use for {label.lower()}.",
                    )
                )
                self.field_combos.append(combo)
                layout.addRow(f"{label}:", combo)

        self.query_edit: QLineEdit | None = None
        if show_query:
            self.query_edit = QLineEdit()
            self.query_edit.setToolTip(CONTROL_TOOLTIPS["Query"])
            self.query_edit.setMinimumWidth(520)
            self.query_edit.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            layout.addRow("Query:", self.query_edit)

        self.deck_filter_edit: QLineEdit | None = None
        if show_deck_filter:
            self.deck_filter_edit = QLineEdit()
            self.deck_filter_edit.setToolTip(CONTROL_TOOLTIPS["Deck Filter"])
            if default_deck_filter:
                self.deck_filter_edit.setText(default_deck_filter)
            layout.addRow("Deck Filter:", self.deck_filter_edit)

        self.tag_filter_edit: QLineEdit | None = None
        if show_tag_filter:
            self.tag_filter_edit = QLineEdit()
            self.tag_filter_edit.setToolTip(CONTROL_TOOLTIPS["Tag Filter"])
            if default_tag_filter:
                self.tag_filter_edit.setText(default_tag_filter)
            layout.addRow("Tag Filter:", self.tag_filter_edit)

        self.dry_run_cb: QCheckBox | None = None
        if show_dry_run:
            self.dry_run_cb = QCheckBox("Dry run")
            self.dry_run_cb.setChecked(default_dry_run)
            self.dry_run_cb.setToolTip(OPTION_TOOLTIPS["Dry run"])
            layout.addRow("", self.dry_run_cb)

        self.backup_cb: QCheckBox | None = None
        if show_backup:
            self.backup_cb = QCheckBox("Create backup before running")
            self.backup_cb.setChecked(default_backup)
            self.backup_cb.setToolTip(OPTION_TOOLTIPS["Create backup before running"])
            layout.addRow("", self.backup_cb)

        self.overwrite_cb: QCheckBox | None = None
        if show_overwrite:
            self.overwrite_cb = QCheckBox("Overwrite target field")
            self.overwrite_cb.setChecked(default_overwrite)
            self.overwrite_cb.setToolTip(OPTION_TOOLTIPS["Overwrite target field"])
            layout.addRow("", self.overwrite_cb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if self.notetype_combo is not None:
            self.notetype_combo.currentTextChanged.connect(self._refresh_fields)
            if self.query_edit is not None:
                self.notetype_combo.currentTextChanged.connect(self._maybe_update_query)
                self.query_edit.textEdited.connect(self._mark_query_dirty)
        if self.query_edit is not None:
            if self.deck_combo is not None and self._use_deck_combo_in_query:
                self.deck_combo.currentTextChanged.connect(
                    self._maybe_update_query_from_filters
                )
            if self.deck_filter_edit is not None:
                self.deck_filter_edit.textEdited.connect(
                    self._maybe_update_query_from_filters
                )
            if self.tag_filter_edit is not None:
                self.tag_filter_edit.textEdited.connect(
                    self._maybe_update_query_from_filters
                )

        self._refresh_fields(self.notetype_combo.currentText() if self.notetype_combo else "")
        if self.query_edit is not None:
            self._initialize_query()
        shared_styling.apply_dialog_theme(self)

    def _mark_query_dirty(self) -> None:
        self._query_dirty = True

    def _initialize_query(self) -> None:
        if self.query_edit is None:
            return
        if self.notetype_combo is not None:
            self._maybe_update_query(self.notetype_combo.currentText())
        elif self._default_query:
            self.query_edit.setText(self._default_query)

    def _default_query_for_notetype(self, notetype: str) -> str:
        if self._default_query_template:
            base = self._default_query_template.format(notetype=notetype)
        else:
            base = self._default_query or (f'note:"{notetype}"' if notetype else "")
        deck_filter = (
            self.deck_filter_edit.text().strip() if self.deck_filter_edit else ""
        )
        deck_combo_value = (
            self.deck_combo.currentText().strip()
            if self._use_deck_combo_in_query and self.deck_combo is not None
            else ""
        )
        tag_filter = self.tag_filter_edit.text().strip() if self.tag_filter_edit else ""
        parts = [base] if base else []
        if deck_filter:
            parts.append(f'deck:"{deck_filter}"')
        elif deck_combo_value:
            parts.append(f'deck:"{deck_combo_value}"')
        if tag_filter:
            tags = [tag for tag in re.split(r"[,\s]+", tag_filter) if tag]
            parts.extend(
                query_term
                for tag in tags
                if (query_term := _query_term_for_tag_filter(tag))
            )
        return " ".join(part for part in parts if part).strip()

    def _maybe_update_query(self, notetype: str) -> None:
        if self.query_edit is None or self._query_dirty:
            return
        auto_query = self._default_query_for_notetype(notetype)
        if auto_query:
            self.query_edit.setText(auto_query)

    def _maybe_update_query_from_filters(self) -> None:
        if self.notetype_combo is not None:
            self._maybe_update_query(self.notetype_combo.currentText())

    def _refresh_fields(self, notetype: str) -> None:
        if not self.field_combos:
            return
        fields = _field_names_for_notetype(notetype)
        for index, combo in enumerate(self.field_combos):
            combo.clear()
            combo.addItems(fields)
            if index < len(self._default_fields):
                desired = self._default_fields[index]
                if desired in fields:
                    combo.setCurrentIndex(fields.index(desired))

    def values(self) -> dict[str, object]:
        return {
            "deck": self.deck_combo.currentText() if self.deck_combo else None,
            "notetype": self.notetype_combo.currentText() if self.notetype_combo else None,
            "fields": [combo.currentText() for combo in self.field_combos],
            "query": self.query_edit.text().strip() if self.query_edit else None,
            "deck_filter": (
                self.deck_filter_edit.text().strip() if self.deck_filter_edit else None
            ),
            "tag_filter": (
                self.tag_filter_edit.text().strip() if self.tag_filter_edit else None
            ),
            "dry_run": self.dry_run_cb.isChecked() if self.dry_run_cb else None,
            "backup": self.backup_cb.isChecked() if self.backup_cb else None,
            "overwrite_target": (
                self.overwrite_cb.isChecked() if self.overwrite_cb else None
            ),
        }


def select_run_options(
    *,
    title: str,
    need_deck: bool = False,
    need_notetype: bool = False,
    field_labels: list[str] | None = None,
    show_query: bool = False,
    default_query: str = "",
    default_query_template: str | None = None,
    show_deck_filter: bool = False,
    show_tag_filter: bool = False,
    default_deck_filter: str | None = None,
    default_tag_filter: str | None = None,
    default_deck: str | None = None,
    use_deck_combo_in_query: bool = False,
    show_dry_run: bool = False,
    default_dry_run: bool = False,
    show_backup: bool = False,
    default_backup: bool = False,
    show_overwrite: bool = False,
    default_overwrite: bool = False,
    default_notetype: str | None = None,
    default_fields: list[str] | None = None,
) -> dict[str, object] | None:
    deck_names = _deck_names() if need_deck else None
    if need_deck and not deck_names:
        showInfo("No decks found.")
        return None

    notetype_names = _notetype_names() if need_notetype else None
    if need_notetype and not notetype_names:
        showInfo("No note types found.")
        return None

    dialog = RunOptionsDialog(
        title=title,
        deck_names=deck_names,
        notetype_names=notetype_names,
        field_labels=field_labels,
        show_query=show_query,
        default_query=default_query,
        default_query_template=default_query_template,
        show_deck_filter=show_deck_filter,
        show_tag_filter=show_tag_filter,
        default_deck_filter=default_deck_filter,
        default_tag_filter=default_tag_filter,
        default_deck=default_deck,
        use_deck_combo_in_query=use_deck_combo_in_query,
        show_dry_run=show_dry_run,
        default_dry_run=default_dry_run,
        show_backup=show_backup,
        default_backup=default_backup,
        show_overwrite=show_overwrite,
        default_overwrite=default_overwrite,
        default_notetype=default_notetype,
        default_fields=default_fields,
    )
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    values = dialog.values()
    if field_labels and any(not field for field in values.get("fields", [])):
        notetype = values.get("notetype") or ""
        if notetype:
            showInfo(f"No fields found in note type: {notetype}")
        else:
            showInfo("No fields found.")
        return None
    if show_query:
        query = str(values.get("query") or "").strip()
        if not query:
            notetype = str(values.get("notetype") or "")
            if default_query_template and notetype:
                query = default_query_template.format(notetype=notetype)
            elif default_query:
                query = default_query
            elif notetype:
                query = f'note:"{notetype}"'
        if not query:
            showInfo("Query is required.")
            return None
        values["query"] = query
    return values


class SettingsDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle("Cloze Formatting Settings")
        tooltip = _tooltip_for_title("Settings")
        if tooltip:
            self.setToolTip(tooltip)

        config = load_config()

        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        info_row = _make_menu_info_row(self, "Settings")
        if info_row is not None:
            layout.addRow("", info_row)

        self.synonym_mode_combo = QComboBox()
        for mode, label in SYNONYM_MODE_LABELS.items():
            self.synonym_mode_combo.addItem(label, mode)
        self.synonym_mode_combo.setCurrentIndex(
            max(
                0,
                self.synonym_mode_combo.findData(config[GREEN_FLAG_SYNONYM_MODE_KEY]),
            )
        )
        self.synonym_mode_combo.setToolTip(
            CONTROL_TOOLTIPS["Green flag synonym mode"]
        )
        layout.addRow("Green flag synonym mode:", self.synonym_mode_combo)

        self.run_startup_green_flag_cb = QCheckBox(
            "Run green-flag synonym replacement on startup"
        )
        self.run_startup_green_flag_cb.setChecked(
            bool(config[RUN_STARTUP_GREEN_FLAG_REPLACEMENT_KEY])
        )
        self.run_startup_green_flag_cb.setToolTip(
            CONTROL_TOOLTIPS["Run startup green-flag replacement"]
        )
        layout.addRow("", self.run_startup_green_flag_cb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        shared_styling.apply_dialog_theme(self)

    def accept(self) -> None:
        save_config(
            {
                GREEN_FLAG_SYNONYM_MODE_KEY: str(
                    self.synonym_mode_combo.currentData()
                    or self.synonym_mode_combo.currentText()
                ),
                RUN_STARTUP_GREEN_FLAG_REPLACEMENT_KEY: bool(
                    self.run_startup_green_flag_cb.isChecked()
                ),
            }
        )
        showInfo("Cloze Formatting settings saved.", parent=self)
        super().accept()


def open_settings_dialog() -> None:
    SettingsDialog().exec()
