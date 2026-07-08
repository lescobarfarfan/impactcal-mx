End-of-session ritual (WORKFLOW.md §2). Execute in order, showing diffs before writing:

1. Produce the closing digest: **Decided / Changed / Open**, one line each, stable `CAL-*` IDs, dates, reference keys (or `[ref?]` / `[eng]`), files touched. No filler.
2. Fold Decided/Changed into `context/DECISIONS.md` (promote, don't duplicate: supersede by editing in place). Show me the diff first.
3. Update, if touched this session: `DATA_CONTRACTS.md` (contracts), `GLOSSARY.md` (+§J phrase), `REFERENCES.md` (verified, else §99 + note in `OQ-CAL-08`), `OPEN_QUESTIONS.md` (opened/closed). Diffs first.
4. Write the session read-log `notes/reading/YYYY-MM-DD_<slug>.md`: per decision, *what to read* (work + specific sections) and *why* (which decision/code it backs), citation keys from REFERENCES. Formatting: one paragraph = one source line; LaTeX math; `## Related` footer linking [[CAL_MOC]] + Home; tags `#arm/cal #type/reading`. Link it from [[CAL_MOC]] §Reading logs.
5. Sanity-check that every new analytical decision has a reference key or `[eng]` (`CAL-GEN-01`); flag violations instead of inventing citations.
6. Commit: one commit for canon/notes, separate commits for code, messages naming the module (`CAL-<MODULE>: …`).
