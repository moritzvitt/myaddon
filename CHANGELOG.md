# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows semantic versioning where practical.

## Unreleased

### Added

- MkDocs configuration for the shared add-on documentation site so this repo's docs can be included in the combined GitHub Pages build.
- Bundled a reusable `shared_menu.py` helper so this add-on can create or reuse the shared `Moritz Add-ons` top-level Anki menu on its own.
- Tooltips for the add-on dialogs and menu actions so each cloze operation explains its fields and safety options on hover.
- Added a Cloze Formatting settings dialog with a `green flag synonym mode` option that controls whether green-flagged cards use the first synonym, first two synonyms, or all available synonyms as their cloze hint.
- Added a Browser action to replace cloze hints on selected notes, with `Synonyms` preselected as the hint source.
- Added a startup setting that automatically replaces cloze hints for green-flagged cards, tags processed notes with `!meta::replace_hints_with_synonyms`, and clears the processed green flags.

### Changed

- Moved the add-on's main-window actions from `Tools` into `Moritz Add-ons -> Cloze Formatting`.
- Moved the Browser `Apply Cloze Pattern (Selected)` entry into the shared Browser `Moritz Add-ons -> Cloze Formatting` submenu.
- Green-flagged cards can now replace the normal cloze hint with text derived from the note's `Synonyms` field, and the green flag is cleared automatically only when that synonym hint was actually applied successfully.
- Renamed the add-on metadata and README examples from `misc-formatting` to `cloze-formatting`.
- Main-menu and Browser dialogs now preselect the current deck or selected-note deck and only preselect a note type when that context resolves to exactly one note type.
- Dialog help was simplified to one general info popup per menu, while field tooltips now describe the specific role of each configured field.
- `Synonyms` HTML is now parsed into comma-separated plain text before hint replacement uses it.

## 0.1.0 - 2026-03-28

### Added

- Starter-repo style repository scaffolding for development, packaging, and release docs.
- A dedicated `addon.py` module with a minimal `__init__.py` entrypoint.
- Default config files for deck and preview-tag behavior.

### Changed

- Narrowed the add-on scope to cloze creation and cloze formatting workflows only.
- Removed unrelated formatting, diagnostics, duplicate-management, and Heisig-specific features.
