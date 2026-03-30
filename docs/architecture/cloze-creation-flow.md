# Cloze Creation Flow

This document reflects the current `create_cloze()` behavior in [`operations/cloze.py`](../../operations/cloze.py).

## Main Flow

Mermaid source: [`cloze-creation-flow.mmd`](./cloze-creation-flow.mmd)

## Notes

- Existing clozes are skipped before any multi-lemma logic runs.
- Multi-lemma notes are split in one run and intentionally left unclozed for that pass.
- After splitting, rerunning `create_cloze()` will process the resulting single-lemma notes.
- `Word Definition` is interpreted line-by-line using `lemma: definition`.
- If a lemma does not find a matching `lemma: definition` entry, the full hint text is used as a fallback.
- Cloze matching prefers:
  1. matching inside a single `<strong>...</strong>` block
  2. longest substring match
  3. exact/token/CJK fallback matching

## Inner Matching Logic

This diagram focuses on the `_apply_cloze_to_note()` decision tree.

Mermaid source: [`cloze-matching-flow.mmd`](./cloze-matching-flow.mmd)

## Single vs Multi Lemma Interaction

This diagram focuses on how single-lemma and multi-lemma creation feed into the same downstream cloze matching logic.

Mermaid source: [`cloze-lemma-paths.mmd`](./cloze-lemma-paths.mmd)
