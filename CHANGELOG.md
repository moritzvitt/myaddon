# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows semantic versioning where practical.

## Unreleased

### Added

- MkDocs configuration for the shared add-on documentation site so this repo's docs can be included in the combined GitHub Pages build.
- Bundled a reusable `shared_menu.py` helper so this add-on can create or reuse the shared `Moritz Add-ons` top-level Anki menu on its own.
- Tooltips for the add-on dialogs and menu actions so each cloze operation explains its fields and safety options on hover.

### Changed

- Moved the add-on's main-window actions from `Tools` into `Moritz Add-ons -> Cloze Formatting`.
- Moved the Browser `Apply Cloze Pattern (Selected)` entry into the shared Browser `Moritz Add-ons -> Cloze Formatting` submenu.
- Renamed the add-on metadata and README examples from `misc-formatting` to `cloze-formatting`.

## 0.1.0 - 2026-03-28

### Added

- Starter-repo style repository scaffolding for development, packaging, and release docs.
- A dedicated `addon.py` module with a minimal `__init__.py` entrypoint.
- Default config files for deck and preview-tag behavior.

### Changed

- Narrowed the add-on scope to cloze creation and cloze formatting workflows only.
- Removed unrelated formatting, diagnostics, duplicate-management, and Heisig-specific features.
