"""Cloze-related operations that work directly on the collection."""

from __future__ import annotations

import re
from typing import Iterable

from ..utils.cloze import longest_substring_match
from ..utils.tags import (
    CLOZE_EXISTING,
    CLOZE_FAILED,
    CLOZE_INCORRECT_PARSE,
    CLOZE_NO_STRONG,
    MULTI_LEMMA,
    NEW_MULTI_LEMMA,
    ORIGINAL_MULTI_LEMMA,
)

STRONG_RE = re.compile(r"<strong>\s*(.*?)\s*</strong>", re.IGNORECASE | re.DOTALL)
TOKEN_SPLIT_RE = re.compile(r"[^\w\u3040-\u30ff\u4e00-\u9fff]+")
CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")


def _parse_hint_entries(hint_text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw_line in (hint_text or "").splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        lemma_part, definition_part = line.split(":", 1)
        lemma = lemma_part.strip()
        definition = definition_part.strip()
        if lemma and definition:
            entries[lemma.casefold()] = definition
    return entries


def _hint_for_lemma(lemma: str, hint_text: str, parsed_hints: dict[str, str]) -> str:
    if not lemma:
        return (hint_text or "").strip()
    return parsed_hints.get(lemma.casefold(), (hint_text or "").strip())


def _clone_note_fields(source_note, target_note) -> None:
    for field_name in source_note.keys():
        target_note[field_name] = source_note[field_name]


def _apply_cloze_to_note(
    note,
    *,
    target_field: str,
    lemma_field: str,
    hint_field: str,
    dry_run: bool,
) -> dict[str, int]:
    original = note[target_field] or ""
    lemma = (note[lemma_field] or "").strip()
    hint = (note[hint_field] or "").strip()

    if "{{c1::" in original:
        if not dry_run:
            note.add_tag(CLOZE_EXISTING)
        return {
            "updated": 0,
            "skipped_no_change": 1,
            "tagged_existing": 1,
            "tagged_no_strong": 0,
            "tagged_failed": 0,
        }

    strong_matches = list(STRONG_RE.finditer(original))
    use_strong = len(strong_matches) == 1
    allow_no_strong_tag = len(strong_matches) == 0

    updated_value = (
        _wrap_strong_cloze_for_lemma(original, lemma, hint) if use_strong else None
    )
    no_strong = updated_value is None

    if updated_value is None:
        longest = longest_substring_match(original, lemma)
        if longest:
            updated_value = _wrap_match_cloze(original, longest, hint)
        else:
            match_result = _find_match_text(original, lemma)
            if match_result:
                match_text, match_kind = match_result
                updated_value = _wrap_match_cloze(original, match_text, hint)
                if match_kind in {"cjk_prefix", "cjk_single"} and not dry_run:
                    note.add_tag(CLOZE_INCORRECT_PARSE)

    if updated_value is None or updated_value == original:
        if not dry_run:
            note.add_tag(CLOZE_FAILED)
        return {
            "updated": 0,
            "skipped_no_change": 0,
            "tagged_existing": 0,
            "tagged_no_strong": 0,
            "tagged_failed": 1,
        }

    if not dry_run:
        note[target_field] = updated_value
        if no_strong and allow_no_strong_tag:
            note.add_tag(CLOZE_NO_STRONG)

    return {
        "updated": 1,
        "skipped_no_change": 0,
        "tagged_existing": 0,
        "tagged_no_strong": int(no_strong and allow_no_strong_tag),
        "tagged_failed": 0,
    }


def _wrap_strong_cloze(value: str, hint: str) -> str | None:
    match = STRONG_RE.search(value or "")
    if not match:
        return None
    inner = match.group(1)
    if not inner.strip():
        return None
    cloze = f"{{{{c1::<strong>{inner}</strong>::{hint}}}}}"
    return value[: match.start()] + cloze + value[match.end() :]


def _wrap_strong_cloze_for_lemma(value: str, lemma: str, hint: str) -> str | None:
    if not value or not lemma:
        return None
    lemma_fold = lemma.casefold()
    for match in STRONG_RE.finditer(value):
        inner = match.group(1)
        if lemma_fold and lemma_fold in (inner or "").casefold():
            cloze = f"{{{{c1::<strong>{inner}</strong>::{hint}}}}}"
            return value[: match.start()] + cloze + value[match.end() :]
    return _wrap_strong_cloze(value, hint)


def _wrap_match_cloze(value: str, match_text: str, hint: str) -> str:
    # If the match lives inside a <strong>...</strong>, wrap the whole strong tag
    # inside the cloze so only the word is bold.
    for match in STRONG_RE.finditer(value):
        inner = match.group(1)
        if match_text and match_text in inner:
            cloze = f"{{{{c1::<strong>{inner}</strong>::{hint}}}}}"
            return value[: match.start()] + cloze + value[match.end() :]
    return value.replace(match_text, f"{{{{c1::{match_text}::{hint}}}}}", 1)


def _find_match_text(value: str, lemma: str) -> tuple[str, str] | None:
    if not value or not lemma:
        return None
    exact_re = re.compile(re.escape(lemma), re.IGNORECASE)
    exact = exact_re.search(value)
    if exact:
        return value[exact.start() : exact.end()], "exact"

    tokens = [t for t in TOKEN_SPLIT_RE.split(lemma) if len(t) >= 3]
    if not tokens:
        pass
    else:
        tokens.sort(key=len, reverse=True)
        token_re = re.compile(re.escape(tokens[0]), re.IGNORECASE)
        token = token_re.search(value)
        if token:
            return value[token.start() : token.end()], "longest_token"

    cjk_chars = CJK_CHAR_RE.findall(lemma)
    if len(cjk_chars) >= 2:
        prefix = "".join(cjk_chars[:2])
        prefix_re = re.compile(re.escape(prefix))
        prefix_match = prefix_re.search(value)
        if prefix_match:
            return value[prefix_match.start() : prefix_match.end()], "cjk_prefix"
    elif len(cjk_chars) == 1:
        single = cjk_chars[0]
        single_re = re.compile(re.escape(single))
        single_match = single_re.search(value)
        if single_match:
            return value[single_match.start() : single_match.end()], "cjk_single"
    return None


def create_cloze(
    col,
    note_ids: Iterable[int],
    *,
    target_field: str = "Cloze",
    lemma_field: str = "Lemma",
    hint_field: str = "Word Definition",
    dry_run: bool = True,
) -> dict[str, int]:
    """
    Example cloze operation using Anki's collection APIs.

    This applies a cloze to <strong> tags when present, otherwise tries to
    match the lemma or its longest token.
    """
    updated = 0
    skipped_missing_field = 0
    skipped_no_change = 0
    tagged_no_strong = 0
    tagged_failed = 0
    tagged_existing = 0
    created_notes = 0
    deferred_multi_lemma = 0

    for nid in note_ids:
        note = col.get_note(nid)
        if target_field not in note or lemma_field not in note or hint_field not in note:
            skipped_missing_field += 1
            continue

        lemma = (note[lemma_field] or "").strip()
        hint = (note[hint_field] or "").strip()
        lemmas = [part.strip() for part in lemma.split(",") if part.strip()]
        if not lemmas:
            skipped_missing_field += 1
            continue

        parsed_hints = _parse_hint_entries(hint)
        lemma_hints = [
            (single_lemma, _hint_for_lemma(single_lemma, hint, parsed_hints))
            for single_lemma in lemmas
        ]

        has_multi_tag = MULTI_LEMMA in note.tags
        if len(lemmas) > 1 and not has_multi_tag:
            created_notes += len(lemmas) - 1

        if len(lemmas) > 1 and not has_multi_tag:
            deferred_multi_lemma += 1

        if len(lemmas) > 1 and not has_multi_tag:
            primary_lemma, primary_hint = lemma_hints[0]
            note[lemma_field] = primary_lemma
            note[hint_field] = primary_hint
            if not dry_run:
                note.add_tag(ORIGINAL_MULTI_LEMMA)
                note.add_tag(MULTI_LEMMA)
            card_ids = note.card_ids()
            deck_id = (
                col.get_card(card_ids[0]).did if card_ids else col.decks.selected()
            )
            for extra_lemma, extra_hint in lemma_hints[1:]:
                new_note = col.new_note(note.model())
                _clone_note_fields(note, new_note)
                new_note.tags = list(note.tags)
                new_note.add_tag(NEW_MULTI_LEMMA)
                new_note.add_tag(MULTI_LEMMA)
                new_note[lemma_field] = extra_lemma
                new_note[hint_field] = extra_hint
                cloze_counts = _apply_cloze_to_note(
                    new_note,
                    target_field=target_field,
                    lemma_field=lemma_field,
                    hint_field=hint_field,
                    dry_run=dry_run,
                )
                tagged_no_strong += cloze_counts["tagged_no_strong"]
                tagged_failed += cloze_counts["tagged_failed"]
                tagged_existing += cloze_counts["tagged_existing"]
                updated += cloze_counts["updated"]
                skipped_no_change += cloze_counts["skipped_no_change"]
                if not dry_run:
                    col.add_note(new_note, deck_id)

        elif len(lemmas) > 1 and has_multi_tag:
            note[lemma_field] = lemma_hints[0][0]
            note[hint_field] = lemma_hints[0][1]

        else:
            note[hint_field] = lemma_hints[0][1]

        cloze_counts = _apply_cloze_to_note(
            note,
            target_field=target_field,
            lemma_field=lemma_field,
            hint_field=hint_field,
            dry_run=dry_run,
        )
        updated += cloze_counts["updated"]
        skipped_no_change += cloze_counts["skipped_no_change"]
        tagged_no_strong += cloze_counts["tagged_no_strong"]
        tagged_failed += cloze_counts["tagged_failed"]
        tagged_existing += cloze_counts["tagged_existing"]

        if not dry_run:
            col.update_note(note)

    return {
        "updated": updated,
        "skipped_missing_field": skipped_missing_field,
        "skipped_no_change": skipped_no_change,
        "tagged_no_strong": tagged_no_strong,
        "tagged_failed": tagged_failed,
        "tagged_existing": tagged_existing,
        "created_notes": created_notes,
        "deferred_multi_lemma": deferred_multi_lemma,
        "dry_run": int(dry_run),
    }
