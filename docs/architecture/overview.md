# Architecture Overview

This add-on is organized around a thin Anki entrypoint, a small registration layer, and focused cloze modules.

## Main Pieces

- [`__init__.py`](../../__init__.py) loads the add-on and calls `register()`.
- [`addon.py`](../../addon.py) is the top-level coordinator that registers menus and hooks.
- [`actions.py`](../../actions.py) contains cloze-related menu and browser action handlers.
- [`dialogs.py`](../../dialogs.py) contains the reusable run-options dialog.
- [`hooks.py`](../../hooks.py) contains browser hook registration.
- [`operations/`](../../operations) contains focused collection-editing routines.
- [`utils/`](../../utils) contains shared helpers for cloze matching and cloze-related tags.

## Runtime Flow

1. Anki imports the add-on package and executes `register()`.
2. Menu actions are added to the Tools menu and browser edit menu.
3. Browser hooks are registered for selected-note cloze actions.
4. Dialog helpers collect user input for each workflow.
5. Each action delegates note updates to a focused module in `operations/`.
