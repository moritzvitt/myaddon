# Misc Formatting

An Anki add-on for batch formatting, tagging, cloze generation, and JP-study maintenance workflows.

This repository now follows the same starter-repo conventions used in your template:

- a minimal add-on entrypoint in [`__init__.py`](./__init__.py)
- the main registration/runtime code in [`addon.py`](./addon.py)
- config defaults in [`config.json`](./config.json) and [`config.md`](./config.md)
- release and architecture docs under [`docs/`](./docs)
- VS Code validation and packaging tasks in [`.vscode/tasks.json`](./.vscode/tasks.json)

## Project Layout

```text
misc-formatting/
├── __init__.py
├── addon.py
├── actions.py
├── dialogs.py
├── hooks.py
├── addon_config.py
├── manifest.json
├── config.json
├── config.md
├── CHANGELOG.md
├── operations/
├── utils/
├── .vscode/
└── docs/
```

## Main Features

- Create cloze deletions from note fields and lemma data
- Strip or rewrite cloze content across note types
- Clean up `<br>` runs and add wrapper markup to fields
- Tag notes based on HTML, Japanese characters, or card type
- Populate Heisig links and unsuspend Heisig cards from JP lemma matches
- Add browser actions for selected-note workflows

## Development Notes

- Anki loads the add-on from the folder root and executes [`__init__.py`](./__init__.py).
- Most collection mutations are implemented in focused modules under [`operations/`](./operations).
- Shared helpers live under [`utils/`](./utils).
- Use the VS Code tasks to validate Python files and package a `.ankiaddon` archive.

## Docs

- Overview: [`docs/README.md`](./docs/README.md)
- Architecture notes: [`docs/architecture/overview.md`](./docs/architecture/overview.md)
- Release text draft: [`docs/release-description.md`](./docs/release-description.md)
