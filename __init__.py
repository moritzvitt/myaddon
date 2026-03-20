from __future__ import annotations

from aqt import gui_hooks, mw, qconnect
from aqt.qt import (
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QInputDialog,
    QLineEdit,
    QSizePolicy,
)
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
from .operations.cloze_hint_replace import replace_cloze_hints
from .operations.field_overwrite import overwrite_field_from_field
from .utils.notes import remove_tag_from_notes, tag_notes


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


def _select_field_name(
    notetype_name: str, *, title: str = "Select Field", label: str = "Field:"
) -> str | None:
    model = mw.col.models.by_name(notetype_name)
    if not model:
        showInfo(f"Note type not found: {notetype_name}")
        return None
    fields = [f["name"] for f in model.get("flds", [])]
    if not fields:
        showInfo(f"No fields found in note type: {notetype_name}")
        return None
    name, ok = QInputDialog.getItem(mw, title, label, fields, 0, False)
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
    source_field = _select_field_name(
        notetype_name, title="Select Source Field", label="Source Field:"
    )
    if not source_field:
        return None
    target_field = _select_field_name(
        notetype_name, title="Select Target Field", label="Target Field:"
    )
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


def _select_overwrite_target(default: bool = False) -> bool | None:
    default_label = "true" if default else "false"
    label, ok = QInputDialog.getItem(
        mw,
        "Overwrite Target Field",
        "Overwrite target field:",
        ["false", "true"],
        1 if default_label == "true" else 0,
        False,
    )
    if not ok or not label:
        return None
    return str(label).lower() == "true"


def _confirm_query_count(action_label: str, query: str, count: int) -> bool:
    return askUser(f"{action_label}\nQuery: {query}\nNotes: {count}")


def _maybe_backup(force: bool | None = None) -> None:
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


def _get_addon_config() -> dict[str, str]:
    config = mw.addonManager.getConfig(__name__) or {}
    if "deck" not in config or not str(config.get("deck") or "").strip():
        config["deck"] = "migaku"
    if "preview_query" not in config or not str(config.get("preview_query") or "").strip():
        config[
            "preview_query"
        ] = "deck:JP -is:suspended -is:buried is:new -flag:3 -flag:2 -flag:4 -flag:1 -flag:6 -tag:marked"
    if "preview_tag" not in config or not str(config.get("preview_tag") or "").strip():
        config["preview_tag"] = "preview"
    if "preview_limit" not in config:
        config["preview_limit"] = 200
    return config


def _save_addon_config(config: dict[str, str]) -> None:
    mw.addonManager.writeConfig(__name__, config)


def _run_open_config() -> None:
    config = _get_addon_config()
    dialog = QDialog(mw)
    dialog.setWindowTitle("MyAddon Configuration")
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
    _save_addon_config(config)
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
        self._query_auto: str | None = None
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
                self.notetype_combo.setCurrentIndex(
                    notetype_names.index(default_notetype)
                )
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
            self.query_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
                self.deck_combo.currentTextChanged.connect(self._maybe_update_query_from_filters)
            if self.deck_filter_edit is not None:
                self.deck_filter_edit.textEdited.connect(self._maybe_update_query_from_filters)
            if self.tag_filter_edit is not None:
                self.tag_filter_edit.textEdited.connect(self._maybe_update_query_from_filters)

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
        else:
            if self._default_query:
                self.query_edit.setText(self._default_query)

    def _default_query_for_notetype(self, notetype: str) -> str:
        if self._default_query_template:
            base = self._default_query_template.format(notetype=notetype)
        else:
            base = self._default_query or (f'note:"{notetype}"' if notetype else "")
        deck_filter = (self.deck_filter_edit.text().strip() if self.deck_filter_edit else "")
        deck_combo_value = (
            self.deck_combo.currentText().strip()
            if self._use_deck_combo_in_query and self.deck_combo is not None
            else ""
        )
        tag_filter = (self.tag_filter_edit.text().strip() if self.tag_filter_edit else "")
        parts = [base] if base else []
        if deck_filter:
            parts.append(f'deck:"{deck_filter}"')
        elif deck_combo_value:
            parts.append(f'deck:"{deck_combo_value}"')
        if tag_filter:
            tags = [t for t in re.split(r"[,\s]+", tag_filter) if t]
            parts.extend(f"tag:{tag}" for tag in tags)
        return " ".join(part for part in parts if part).strip()

    def _maybe_update_query(self, notetype: str) -> None:
        if self.query_edit is None:
            return
        if self._query_dirty:
            return
        auto_query = self._default_query_for_notetype(notetype)
        if auto_query:
            self.query_edit.setText(auto_query)
            self._query_auto = auto_query

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
            "deck_filter": self.deck_filter_edit.text().strip()
            if self.deck_filter_edit
            else None,
            "tag_filter": self.tag_filter_edit.text().strip() if self.tag_filter_edit else None,
            "dry_run": self.dry_run_cb.isChecked() if self.dry_run_cb else None,
            "backup": self.backup_cb.isChecked() if self.backup_cb else None,
            "overwrite_target": self.overwrite_cb.isChecked() if self.overwrite_cb else None,
        }


def _select_run_options(
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


def _run_create_cloze_for_deck() -> None:
    options = _select_run_options(
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
    notetype_name = str(options["notetype"])
    deck_name = str(options["deck"])
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
        _maybe_backup(force=True)
    result = create_cloze(
        mw.col,
        note_ids,
        target_field=target_field,
        lemma_field=lemma_field,
        hint_field=hint_field,
        dry_run=dry_run,
    )
    showInfo(f"create_cloze finished: {result}")


action = QAction("Create Cloze (Query)", mw)
qconnect(action.triggered, _run_create_cloze_for_deck)
mw.form.menuTools.addAction(action)


action = QAction("MyAddon Configuration", mw)
qconnect(action.triggered, _run_open_config)
mw.form.menuTools.addAction(action)


def _run_suspend_duplicates() -> None:
    options = _select_run_options(
        title="Suspend Duplicates",
        need_deck=True,
        show_backup=True,
        default_backup=False,
    )
    if not options:
        return
    deck_name = str(options["deck"])
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
    if options.get("backup"):
        _maybe_backup(force=True)
    result = suspend_duplicates(mw.col, query=query, dry_run=False)
    showInfo(f"suspend_duplicates finished: {result}")


action = QAction("Suspend Duplicates", mw)
qconnect(action.triggered, _run_suspend_duplicates)
mw.form.menuTools.addAction(action)


def _run_wrap_left_div_for_notetype() -> None:
    options = _select_run_options(
        title="Wrap Field Left Div (Note Type)",
        need_notetype=True,
        field_labels=["Field"],
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
    )
    if not options:
        return
    notetype_name = str(options["notetype"])
    field_name = str(options["fields"][0])
    query = str(options["query"] or "")
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        _maybe_backup(force=True)
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
    options = _select_run_options(
        title="Cleanup <br> Runs (Note Type)",
        need_notetype=True,
        field_labels=["Field"],
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
    )
    if not options:
        return
    notetype_name = str(options["notetype"])
    field_name = str(options["fields"][0])
    query = str(options["query"] or "")
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        _maybe_backup(force=True)
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
    options = _select_run_options(
        title="Check Square Brackets (Note Type)",
        need_notetype=True,
        field_labels=["Field"],
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
    )
    if not options:
        return
    notetype_name = str(options["notetype"])
    field_name = str(options["fields"][0])
    query = str(options["query"] or "")
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        _maybe_backup(force=True)
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
    options = _select_run_options(
        title="Tag No HTML (Note Type)",
        need_notetype=True,
        field_labels=["Field"],
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
    )
    if not options:
        return
    notetype_name = str(options["notetype"])
    field_name = str(options["fields"][0])
    query = str(options["query"] or "")
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        _maybe_backup(force=True)
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
    options = _select_run_options(
        title="Tag Japanese Characters (Note Type)",
        need_notetype=True,
        field_labels=["Field"],
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_dry_run=False,
        default_backup=False,
    )
    if not options:
        return
    notetype_name = str(options["notetype"])
    field_name = str(options["fields"][0])
    query = str(options["query"] or "")
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        _maybe_backup(force=True)
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
    options = _select_run_options(
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
    notetype_name = str(options["notetype"])
    source_field = str(options["fields"][0])
    target_field = str(options["fields"][1])
    query = str(options["query"] or "")
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    overwrite_target = bool(options.get("overwrite_target"))
    if not dry_run and options.get("backup"):
        _maybe_backup(force=True)
    result = strip_cloze_to_field(
        mw.col,
        note_ids,
        source_field=source_field,
        target_field=target_field,
        overwrite_target=overwrite_target,
        dry_run=dry_run,
    )
    showInfo(f"strip_cloze_to_field finished: {result}")


action = QAction("Strip Cloze to Field (Note Type)", mw)
qconnect(action.triggered, _run_strip_cloze_for_notetype)
mw.form.menuTools.addAction(action)


def _run_replace_cloze_hints_for_notetype() -> None:
    options = _select_run_options(
        title="Replace Cloze Hints (Note Type)",
        need_notetype=True,
        field_labels=["Hint Field"],
        show_query=True,
        show_deck_filter=True,
        show_tag_filter=True,
        show_dry_run=True,
        show_backup=True,
        default_query_template='note:"{notetype}" deck:migaku tag:meta::multi_lemma',
        default_dry_run=False,
        default_backup=False,
    )
    if not options:
        return
    notetype_name = str(options["notetype"])
    hint_field = str(options["fields"][0])
    query = str(options["query"] or "")
    note_ids = list(mw.col.find_notes(query))
    if not note_ids:
        showInfo(f"No notes found for query: {query}")
        return
    dry_run = bool(options.get("dry_run"))
    if not dry_run and options.get("backup"):
        _maybe_backup(force=True)
    result = replace_cloze_hints(
        mw.col,
        note_ids,
        cloze_field="Cloze",
        hint_field=hint_field,
        dry_run=dry_run,
    )
    showInfo(f"replace_cloze_hints finished: {result}")


action = QAction("Replace Cloze Hints (Note Type)", mw)
qconnect(action.triggered, _run_replace_cloze_hints_for_notetype)
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
    options = _select_run_options(
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
                if any(mw.col.decks.name(mw.col.get_card(cid).did) == deck_name for cid in card_ids):
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
        _maybe_backup(force=True)
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


def _run_overwrite_field_for_browser(browser) -> None:
    note_ids = _browser_selected_note_ids(browser)
    if not note_ids:
        showInfo("No notes selected.")
        return
    options = _select_run_options(
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
        _maybe_backup(force=True)
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


def _add_browser_menu(browser) -> None:
    action = QAction("Apply Cloze Pattern (Selected)", browser)
    qconnect(action.triggered, lambda: _run_create_cloze_for_browser(browser))
    browser.form.menuEdit.addAction(action)
    action = QAction("Overwrite Field From Field (Selected)", browser)
    qconnect(action.triggered, lambda: _run_overwrite_field_for_browser(browser))
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


def _auto_tag_preview_on_startup() -> None:
    query = (
        "deck:JP -is:suspended -is:buried is:new "
        "-flag:3 -flag:2 -flag:4 -flag:1 -flag:6 -tag:marked"
    )
    tag = "preview"
    limit = 200

    note_ids_with_tag = mw.col.find_notes(f"tag:{tag}")
    if note_ids_with_tag:
        remove_tag_from_notes(mw.col, note_ids_with_tag, tag)

    card_ids = list(mw.col.find_cards(query, order="c.due asc"))
    if not card_ids:
        return
    note_ids = {mw.col.get_card(cid).nid for cid in card_ids[:limit]}
    if not note_ids:
        return
    added = tag_notes(mw.col, note_ids, tag)
    if added:
        tooltip("Added preview tag", period=2000)


gui_hooks.profile_did_open.append(lambda: _auto_tag_preview_on_startup())
