# OBSIDIAN_SETUP — vault conventions

Open the repo root as a vault. `context/`, `notes/`, `literature/`, and the root hubs form the
graph; `src/`, `data/`, `results/` are not notes.

## 1. Linking
- **Wikilinks by basename**: `[[DECISIONS]]`, `[[CAL_MOC]]`, `[[Calibracion_Impacto_Mexico_Master]]` — resolve across folders, survive moves.
- Every note ends with a `## Related` footer linking its neighbours and home (`Home: [[_INDEX]]`), and carries `#arm/cal` + `#type/<decisions|contracts|glossary|references|open-questions|workflow|theory|reading|pipeline|readme>` tags.
- `[[CAL_MOC]]` is the hub: every `notes/*` note must be reachable from it. `_INDEX` branches to the MOC and the canon.
- Renaming/moving: update inbound links (Obsidian rename updates backlinks). GitHub not rendering wikilinks is expected — the vault is Obsidian-first.

## 2. Formatting convention
- One paragraph / one list item = **one source line** (Obsidian renders single newlines as breaks; no hard-wrapping). Canon files inherited hard-wrapped style is tolerated; new notes follow this rule.
- **Math in LaTeX** (`$…$`, `$$…$$`); backticks only for code identifiers, paths, canon IDs.
- Diagrams in **Mermaid** fenced blocks; file trees as plain code blocks. **All Mermaid node/subgraph labels go in double quotes** (`A["texto"]`): unquoted labels with non-ASCII glyphs (`×`, `↔`, `∝`) are a lexical error in the Mermaid bundled with Obsidian (verified on 10.2.3).

## 3. What's ignored
`.obsidian/workspace*` and machine-local config are git-ignored; conventions live here, not in `.obsidian/`.

## Related
[[_INDEX]] · [[00_README_CONTEXT]] · [[CAL_MOC]]
#arm/cal #type/workflow
