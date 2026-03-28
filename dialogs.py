from __future__ import annotations

import re

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSizePolicy,
)
from aqt.utils import showInfo

from .addon_config import get_addon_config, save_addon_config


def open_config_dialog() -> None:
    config = get_addon_config()
    dialog = QDialog(mw)
    dialog.setWindowTitle("Misc Formatting Configuration")
    layout = QFormLayout(dialog)
    layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

    deck_edit = QLineEdit()
    deck_edit.setText(str(config.get("deck", "migaku")))
    layout.addRow("Deck:", deck_edit)

    preview_query_edit = QLineEdit()
    preview_query_edit.setText(str(config.get("preview_query", "")))
    layout.addRow("Preview Query:", preview_query_edit)

    preview_tag_edit = QLineEdit()
    preview_tag_edit.setText(str(config.get("preview_tag", "")))
    layout.addRow("Preview Tag:", preview_tag_edit)

    preview_limit_edit = QLineEdit()
    preview_limit_edit.setText(str(config.get("preview_limit", 200)))
    layout.addRow("Preview Limit:", preview_limit_edit)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok
        | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return

    config["deck"] = deck_edit.text().strip() or "migaku"
    config["preview_query"] = preview_query_edit.text().strip()
    config["preview_tag"] = preview_tag_edit.text().strip()
    try:
        config["preview_limit"] = max(0, int(preview_limit_edit.text().strip() or "0"))
    except ValueError:
        config["preview_limit"] = 200
    save_addon_config(config)
    showInfo("Configuration saved.")


def _deck_names() -> list[str]:
    decks = mw.col.decks.all_names_and_ids()
    return sorted(d.name for d in decks)


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
        self._default_query = default_query
        self._default_query_template = default_query_template
        self._query_dirty = False
        self._default_fields = default_fields or []
        self._use_deck_combo_in_query = use_deck_combo_in_query

        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.deck_combo: QComboBox | None = None
        if deck_names is not None:
            self.deck_combo = QComboBox()
            self.deck_combo.addItems(deck_names)
            layout.addRow("Deck:", self.deck_combo)

        self.notetype_combo: QComboBox | None = None
        if notetype_names is not None:
            self.notetype_combo = QComboBox()
            self.notetype_combo.addItems(notetype_names)
            if default_notetype and default_notetype in notetype_names:
                self.notetype_combo.setCurrentIndex(notetype_names.index(default_notetype))
            layout.addRow("Note Type:", self.notetype_combo)

        self.field_combos: list[QComboBox] = []
        if field_labels:
            for label in field_labels:
                combo = QComboBox()
                self.field_combos.append(combo)
                layout.addRow(f"{label}:", combo)

        self.query_edit: QLineEdit | None = None
        if show_query:
            self.query_edit = QLineEdit()
            self.query_edit.setMinimumWidth(520)
            self.query_edit.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            layout.addRow("Query:", self.query_edit)

        self.deck_filter_edit: QLineEdit | None = None
        if show_deck_filter:
            self.deck_filter_edit = QLineEdit()
            if default_deck_filter:
                self.deck_filter_edit.setText(default_deck_filter)
            layout.addRow("Deck Filter:", self.deck_filter_edit)

        self.tag_filter_edit: QLineEdit | None = None
        if show_tag_filter:
            self.tag_filter_edit = QLineEdit()
            if default_tag_filter:
                self.tag_filter_edit.setText(default_tag_filter)
            layout.addRow("Tag Filter:", self.tag_filter_edit)

        self.dry_run_cb: QCheckBox | None = None
        if show_dry_run:
            self.dry_run_cb = QCheckBox("Dry run")
            self.dry_run_cb.setChecked(default_dry_run)
            layout.addRow("", self.dry_run_cb)

        self.backup_cb: QCheckBox | None = None
        if show_backup:
            self.backup_cb = QCheckBox("Create backup before running")
            self.backup_cb.setChecked(default_backup)
            layout.addRow("", self.backup_cb)

        self.overwrite_cb: QCheckBox | None = None
        if show_overwrite:
            self.overwrite_cb = QCheckBox("Overwrite target field")
            self.overwrite_cb.setChecked(default_overwrite)
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
            parts.extend(f"tag:{tag}" for tag in tags)
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
