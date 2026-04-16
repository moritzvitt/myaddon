# Cloze Formatting

This add-on is built for a workflow where you export sentence cards from Migaku into Anki, but the exported sentence does not yet contain the Anki cloze markup.

In that setup, you often have the target word in one field and the sentence in another field, and you need to combine both pieces to generate the actual cloze card. This add-on does that automatically: it looks for the lemma or target word inside the sentence and wraps the match in Anki's cloze syntax. The selected hint field becomes the cloze hint, so you do not have to build clozes by hand after every export.

<p align="center">
  <img src="./media/Screenshot%202026-04-16%20at%2012.02.10.png" alt="Cloze Formatting dialog for creating cloze cards from imported sentence notes" width="900">
</p>

<p align="center">
  <img src="./media/Screenshot%202026-04-16%20at%2012.03.29.png" alt="Cloze Formatting browser actions and hint replacement workflow" width="900">
</p>

Available options include:

- automatic cloze creation from a word field plus a sentence field
- query-based cloze creation for a deck or filtered batch
- Browser actions for selected-note cloze generation
- Browser actions for selected-note cloze hint replacement
- bulk replacement of cloze hints from another field such as `Word Definition` or `Synonyms`
- green-flag workflow to gradually switch cards from translation-based hints to synonym-based hints
- configurable synonym mode using the first synonym, first two synonyms, or all available synonyms
- startup automation for processing green-flagged cards and clearing their flags after successful replacement
- cloze stripping into a plain-text target field
- configuration dialogs under `Moritz Add-ons`

This is useful if you import a lot of content from Migaku, want a faster path from exported sentence card to finished cloze card, and want a few extra maintenance tools for adjusting hints and cleaning up cloze fields afterward.
