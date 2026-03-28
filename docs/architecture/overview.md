# Architecture Overview

This add-on is organized around a thin Anki entrypoint, a small registration layer, and focused support modules.

## Main Pieces

- [`__init__.py`](../../__init__.py) loads the add-on and calls `register()`.
- [`addon.py`](../../addon.py) is the top-level coordinator that registers menus and hooks.
- [`actions.py`](../../actions.py) contains menu and browser action handlers.
- [`dialogs.py`](../../dialogs.py) contains the config dialog and reusable run-options dialog.
- [`hooks.py`](../../hooks.py) contains browser/profile hook registration and startup behavior.
- [`addon_config.py`](../../addon_config.py) contains add-on config loading and persistence.
- [`operations/`](../../operations) contains focused collection-editing routines.
- [`utils/`](../../utils) contains shared helpers for config defaults, note/tag handling, HTML helpers, and cloze matching.

## Runtime Flow

1. Anki imports the add-on package and executes `register()`.
2. Menu actions are added to the Tools menu and browser edit menu.
3. Browser/profile hooks are registered for selected-note actions and startup automation.
4. Dialog helpers collect user input for each workflow.
5. Each action delegates note updates to a focused module in `operations/`.
