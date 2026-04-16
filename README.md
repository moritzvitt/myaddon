# Cloze Formatting

<p align="center">
  <a href="https://buymeacoffee.com/moritzowitsch">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Buy Me a Coffee" />
  </a>
  <a href="https://github.com/moritzvitt">
    <img src="https://img.shields.io/badge/GitHub-moritzvitt-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub moritzvitt" />
  </a>
</p>

An Anki add-on focused on cloze creation and cloze maintenance workflows.

## Project Layout

```text
cloze-formatting/
├── __init__.py
├── addon.py
├── actions.py
├── dialogs.py
├── hooks.py
├── manifest.json
├── CHANGELOG.md
├── operations/
├── utils/
└── docs/
```

## Main Features

- Create cloze deletions from note fields and lemma data
- Replace cloze hints across note types
- Strip cloze markup into target fields
- Add a browser action for selected-note cloze application

## Development Notes

- Anki loads the add-on from the folder root and executes [`__init__.py`](./__init__.py).
- Most collection mutations are implemented in focused modules under [`operations/`](./operations).
- Shared cloze helpers live under [`utils/`](./utils).
- Use the VS Code tasks to validate Python files and package a `.ankiaddon` archive.

## Docs

- Overview: [`docs/README.md`](./docs/README.md)
- Architecture notes: [`docs/architecture/overview.md`](./docs/architecture/overview.md)
- Release text draft: [`docs/release-description.md`](./docs/release-description.md)
