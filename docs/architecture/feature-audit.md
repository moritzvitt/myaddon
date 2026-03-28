# Feature Audit

This document audits the current user-facing feature set of the add-on and sorts each feature into one of four buckets:

- `keep`: core to the add-on's identity
- `move out`: useful, but belongs in a separate add-on or domain-specific tool
- `hide`: keep in the codebase, but reduce visibility in the main UI
- `delete`: remove because it adds more maintenance cost than product value

## Current Surface Area

### Tools Menu Actions

- Create Cloze (Query)
- Misc Formatting Configuration
- Wrap Field Left Div (Note Type)
- Cleanup `<br>` Runs (Note Type)
- Check Square Brackets (Note Type)
- Tag No HTML (Note Type)
- Tag Japanese Characters (Note Type)
- Tag Word vs Sentence Cards (Note Type)
- Strip Cloze to Field (Note Type)
- Replace Cloze Hints (Note Type)
- Unsuspend Heisig by JP Lemmas
- Populate Heisig Links from JP
- Suspend Duplicates
  Only appears when `operations/duplicates.py` exists.

### Browser Menu Actions

- Apply Cloze Pattern (Selected)
- Overwrite Field From Field (Selected)

### Startup / Hook Behavior

- Browser `limit:N` search modifier
- Auto-wrap `Notes` and `Grammar` fields on profile open
- Auto-tag preview notes on profile open

## Recommendation Summary

### Keep

- Create Cloze (Query)
- Apply Cloze Pattern (Selected)
- Replace Cloze Hints (Note Type)
- Strip Cloze to Field (Note Type)
- Wrap Field Left Div (Note Type)
- Cleanup `<br>` Runs (Note Type)
- Misc Formatting Configuration

### Move Out

- Unsuspend Heisig by JP Lemmas
- Populate Heisig Links from JP
- Auto-tag preview notes on profile open

### Hide

- Check Square Brackets (Note Type)
- Tag No HTML (Note Type)
- Tag Japanese Characters (Note Type)
- Tag Word vs Sentence Cards (Note Type)
- Overwrite Field From Field (Selected)
- Browser `limit:N` search modifier
- Auto-wrap `Notes` and `Grammar` fields on profile open

### Delete

- Suspend Duplicates

## Detailed Recommendations

### Keep

#### Create Cloze (Query)

Recommendation: `keep`

Why:
- This is the clearest core feature in the add-on.
- It matches the current direction of your recent work on lemma-aware cloze processing.
- It is understandable as a batch formatting/transformation workflow.

#### Apply Cloze Pattern (Selected)

Recommendation: `keep`

Why:
- It is the browser-scoped companion to the main cloze workflow.
- It gives you a precise, low-risk way to run the core feature on selected notes.
- Keeping both query-wide and selection-based entry points is reasonable.

#### Replace Cloze Hints (Note Type)

Recommendation: `keep`

Why:
- This is directly related to cloze authoring and maintenance.
- It fits the same mental model as creating and cleaning clozes.
- It becomes even more relevant with lemma-specific definition hints.

#### Strip Cloze to Field (Note Type)

Recommendation: `keep`

Why:
- This is a useful companion utility for cloze workflows.
- It supports data migration and cleanup without being too domain-specific.

#### Wrap Field Left Div (Note Type)

Recommendation: `keep`

Why:
- This is a true formatting operation and matches the repo name.
- It is broad enough to justify inclusion in a formatting utility add-on.

#### Cleanup `<br>` Runs (Note Type)

Recommendation: `keep`

Why:
- This is another straightforward formatting cleanup operation.
- It is easy to explain and close in scope to the rest of the formatting tools.

#### Misc Formatting Configuration

Recommendation: `keep`

Why:
- If startup behavior remains in this add-on, config belongs here.
- It is infrastructure, not scope creep by itself.

### Move Out

#### Unsuspend Heisig by JP Lemmas

Recommendation: `move out`

Why:
- This is highly domain-specific.
- It depends on a particular Japanese study workflow and deck setup.
- It does not read like a generic formatting or cloze feature.

#### Populate Heisig Links from JP

Recommendation: `move out`

Why:
- This is even more specialized than the unsuspend action.
- It is effectively its own study-automation feature, not a formatting action.
- It would be much easier to maintain and reason about in a dedicated Heisig/JP helper add-on.

#### Auto-tag Preview Notes On Startup

Recommendation: `move out`

Why:
- This is workflow automation tied to a specific study process, not formatting.
- It acts automatically on profile open, which raises the risk and surprise factor.
- If the Heisig/JP workflows move out, this likely belongs with them or in a separate preview helper.

### Hide

#### Check Square Brackets (Note Type)

Recommendation: `hide`

Why:
- This seems like a QA/debugging tool rather than a daily user-facing feature.
- It may still be useful, but it does not need top-level visibility.

Suggested treatment:
- Move under an `Advanced`, `QA`, or `Diagnostics` submenu.

#### Tag No HTML (Note Type)

Recommendation: `hide`

Why:
- This is a diagnostic tagging pass, not a primary transformation.
- It is helpful for investigation but not part of the main product story.

#### Tag Japanese Characters (Note Type)

Recommendation: `hide`

Why:
- Useful for analysis and cleanup, but narrower and more technical than the main formatting features.
- Better framed as a utility than as a headline action.

#### Tag Word vs Sentence Cards (Note Type)

Recommendation: `hide`

Why:
- This is a classification tool, not a formatting tool.
- It could still be helpful, but it likely belongs in a secondary tools section.

#### Overwrite Field From Field (Selected)

Recommendation: `hide`

Why:
- It is powerful and potentially destructive.
- It looks more like a one-off migration utility than a core add-on identity feature.
- Keeping it accessible only in the browser is already a good constraint.

Suggested treatment:
- Keep it browser-only and move it under an advanced submenu or rename it to sound more clearly like a migration tool.

#### Browser `limit:N` Search Modifier

Recommendation: `hide`

Why:
- This is clever, but invisible features are easy to forget and hard to onboard.
- It may still be worth keeping for personal use.

Suggested treatment:
- Document it clearly and treat it as an advanced power-user feature.

#### Auto-wrap `Notes` and `Grammar` On Startup

Recommendation: `hide`

Why:
- It mutates note data automatically on profile open, which is high-impact behavior.
- Even if you keep it, it should not be part of the “main identity” of the add-on.

Suggested treatment:
- Make it explicitly configurable and consider disabling it by default.

### Delete

#### Suspend Duplicates

Recommendation: `delete`

Why:
- The implementation is currently missing.
- The feature is conceptually separate from formatting/cloze work.
- Missing-code features create mental overhead even when disabled.

Suggested treatment:
- Delete it from this add-on unless you already know you want it in a dedicated duplicate-management tool.

## Suggested Product Shape

If you keep this as a single add-on, the cleanest product story would be:

> An Anki add-on for cloze generation and note-field formatting utilities.

That suggests this primary scope:

- cloze creation
- cloze hint maintenance
- cloze field extraction
- field formatting cleanup

And this secondary scope:

- QA/diagnostic tools, but less visible

And this out-of-scope area:

- Heisig-specific study automations
- deck-specific preview automation
- duplicate management

## Suggested Next Step

If you want to simplify without fully splitting the repo yet, the lowest-friction next move would be:

1. Keep the `keep` set in the main Tools menu.
2. Move the `hide` set under an `Advanced` or `Diagnostics` submenu.
3. Remove the `delete` set.
4. Open a separate add-on or repo folder later for the `move out` set.
