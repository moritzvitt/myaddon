# Cloze Creation Flow

This diagram reflects the current `create_cloze()` behavior in [`operations/cloze.py`](../../operations/cloze.py).

```mermaid
flowchart TD
    A[Start create_cloze<br/>for each note id] --> B{Target / lemma / hint<br/>fields exist?}
    B -- No --> B1[Increment skipped_missing_field] --> Z
    B -- Yes --> C[Read Cloze, Lemma,<br/>Word Definition]
    C --> D{Lemma list empty?}
    D -- Yes --> D1[Increment skipped_missing_field] --> Z
    D -- No --> E[Split Lemma by commas]
    E --> F[Parse Word Definition lines<br/>as lemma: definition]
    F --> G[Map each lemma to its hint]
    G --> H{Multiple lemmas<br/>and no MULTI_LEMMA tag?}

    H -- Yes --> I[Mark original note with first lemma<br/>and first matching definition]
    I --> J[For each extra lemma:<br/>clone note, set lemma + hint]
    J --> K[Apply cloze logic to each cloned note]
    K --> L{dry_run?}
    L -- No --> M[Add cloned notes to collection]
    L -- Yes --> N[Count results only]
    M --> O[Apply cloze logic to original note]
    N --> O

    H -- No --> P{Multiple lemmas<br/>already tagged?}
    P -- Yes --> Q[Keep first lemma + first matching definition]
    P -- No --> R[Use single lemma<br/>and matching definition]
    Q --> O
    R --> O

    O --> S{Cloze already exists?}
    S -- Yes --> S1[Tag CLOZE_EXISTING<br/>increment skipped_no_change] --> Y
    S -- No --> T[Try strong-tag cloze<br/>for matching lemma]
    T --> U{Updated?}
    U -- Yes --> Y
    U -- No --> V[Try longest_substring_match]
    V --> W{Updated?}
    W -- Yes --> Y
    W -- No --> X[Try exact/token/CJK fallback match]
    X --> X1{Updated?}
    X1 -- No --> X2[Tag CLOZE_FAILED] --> Y
    X1 -- Yes --> X3[If CJK fallback used:<br/>tag CLOZE_INCORRECT_PARSE] --> Y

    Y[If update succeeded:<br/>write cloze, maybe tag CLOZE_NO_STRONG,<br/>update counters and save note when not dry_run] --> Z[Next note / end]
```

## Notes

- Multi-lemma notes are split before the main cloze application path runs.
- `Word Definition` is interpreted line-by-line using `lemma: definition`.
- If a lemma does not find a matching `lemma: definition` entry, the full hint text is used as a fallback.
- Cloze matching prefers:
  1. matching inside a single `<strong>...</strong>` block
  2. longest substring match
  3. exact/token/CJK fallback matching

## Inner Matching Logic

This diagram focuses on the `_apply_cloze_to_note()` decision tree.

```mermaid
flowchart TD
    A[Start _apply_cloze_to_note] --> B{Already contains<br/>{{c1:: ?}}
    B -- Yes --> B1[Tag CLOZE_EXISTING<br/>return skipped_no_change]
    B -- No --> C[Count strong tags]
    C --> D{Exactly one<br/><strong>...</strong> block?}
    D -- Yes --> E[Try _wrap_strong_cloze_for_lemma]
    D -- No --> F[Skip strong-first path]
    E --> G{Updated?}
    F --> G
    G -- Yes --> H[Success]
    G -- No --> I[Try longest_substring_match]
    I --> J{Updated?}
    J -- Yes --> H
    J -- No --> K[Try _find_match_text<br/>exact / longest token / CJK]
    K --> L{Updated?}
    L -- No --> M[Tag CLOZE_FAILED<br/>return failed]
    L -- Yes --> N{CJK prefix/single<br/>fallback used?}
    N -- Yes --> O[Tag CLOZE_INCORRECT_PARSE]
    N -- No --> P[Continue]
    O --> H
    P --> H
    H --> Q{No strong tag used<br/>and zero strong blocks?}
    Q -- Yes --> R[Tag CLOZE_NO_STRONG]
    Q -- No --> S[No extra tag]
    R --> T[Write updated cloze<br/>when not dry_run]
    S --> T
    T --> U[Return success counts]
```
