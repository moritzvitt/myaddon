# Cloze Formatting

<p align="center">
  <a href="https://buymeacoffee.com/moritzowitsch">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Buy Me a Coffee" />
  </a>
  <a href="https://github.com/moritzvitt">
    <img src="https://img.shields.io/badge/GitHub-moritzvitt-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub moritzvitt" />
  </a>
</p>

This add-on is built for a workflow where you export sentence cards from Migaku into Anki, but the exported sentence does not yet contain the Anki cloze markup.

If you want a more polished and consistent look across my add-ons, you can also install my `Global Styling` add-on. It lets you apply a shared design on top of supported add-ons without changing their functionality.

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

This is useful if you import a lot of content from Migaku, want a faster path from exported sentence card to finished cloze card, and want a few extra maintenance tools for adjusting hints and cleaning up cloze fields afterward.
