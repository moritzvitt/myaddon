Project Notes (myaddon)

Quick Map
- Entry point: __init__.py
- Operations: operations/*
- Shared helpers: utils/*
- Tags: utils/tags.py

Main Flows (Menu Actions)
- Create Cloze (Deck)
  __init__:_run_create_cloze_for_deck -> operations/cloze.py:create_cloze
- Apply Cloze Pattern (Selected)
  __init__:_run_create_cloze_for_browser -> operations/cloze.py:create_cloze
- Strip Cloze to Field (Note Type)
  __init__:_run_strip_cloze_for_notetype -> operations/cloze_strip.py:strip_cloze_to_field
- Replace Cloze Hints (Note Type)
  __init__:_run_replace_cloze_hints_for_notetype -> operations/cloze_hint_replace.py:replace_cloze_hints
- Wrap Field Left Div (Note Type)
  __init__:_run_wrap_left_div_for_notetype -> operations/field_wrap.py:wrap_field_in_left_div
- Cleanup <br> Runs (Note Type)
  __init__:_run_cleanup_br_runs_for_notetype -> operations/br_cleanup.py:cleanup_br_runs
- Check Square Brackets (Note Type)
  __init__:_run_check_brackets_for_notetype -> operations/bracket_check.py:check_square_brackets
- Tag No HTML (Note Type)
  __init__:_run_no_html_check_for_notetype -> operations/no_html_check.py:tag_no_html
- Tag Japanese Characters (Note Type)
  __init__:_run_japanese_char_check_for_notetype -> operations/japanese_char_check.py:tag_contains_japanese
- Suspend Duplicates
  __init__:_run_suspend_duplicates -> operations/duplicates.py:suspend_duplicates
- Unsuspend Heisig by JP Lemmas
  __init__:_run_unsuspend_heisig_by_jp -> operations/heisig_unsuspend.py:unsuspend_heisig_by_jp_lemmas
- Populate Heisig Links from JP
  __init__:_run_heisig_links_by_jp -> operations/heisig_links.py:populate_heisig_links_by_jp_lemmas

Key Behaviors
- Backups: __init__._maybe_backup() is used before most destructive actions.
- Dry-run: Most actions ask for dry-run and return a summary dict.
- Multi-lemma handling (create_cloze):
  If Lemma contains commas, the note is split and tagged as meta::multi_lemma.
  Cloze patterns are deferred for multi-lemma notes (no cloze applied yet).

Notes/Fields You Care About
- Common fields: Lemma, Cloze, Word Definition (varies by note type).
- Tags: utils/tags.py (meta::* tags used across operations).

Places to Start When Debugging
- UI wiring and prompts: __init__.py
- Cloze behavior: operations/cloze.py and utils/cloze.py
- Tag definitions: utils/tags.py
