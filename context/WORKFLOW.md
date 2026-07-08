# WORKFLOW — Keeping the canon alive & the project reproducible

Working discipline for `impactcal-mx`. ~2 minutes per session beats reconstructing context later.

---

## 0. The one rule

**This branch lives in ONE place** — this repo + its claude.ai project. If the branch merges into
`climateCCR` later (`OQ-CAL-12`), the merge imports this canon; it is never re-derived from memory.

## 1. The canon

`context/` is the single source of truth for decisions, contracts, vocabulary, references, open
items, and this workflow. Living documents — edit in place. Code is its own source of truth in
`src/impactcal/`; theory in `notes/theory/`; papers in `literature/`.

## 2. End-of-session ritual (before closing any working session)

1. Produce the **closing digest** (template below) — `/digest` automates 1–7.
2. Fold into `DECISIONS.md` (one line per point: stable `CAL-*` ID, date, reference key).
3. Contract changed (name/grain/column/units)? → edit `DATA_CONTRACTS.md`.
4. New term? → `GLOSSARY.md` (and its §J search phrase).
5. Reference used/confirmed? → `REFERENCES.md` (unconfirmed → §99 + `OQ-CAL-08`).
6. Something opened/closed? → `OPEN_QUESTIONS.md`.
7. Write the **session read-log** `notes/reading/YYYY-MM-DD_<slug>.md`: per decision, *what to
   read* (work + sections) and *why* (which decision/code it backs), citation keys from
   `REFERENCES.md`. Always, even unasked.
8. Commit, message naming the module (`CAL-WIND: freeze timestep after convergence test`).

> **Promote, don't duplicate.** A superseding decision edits the old line in place.

### Digest template

> Before we close: give me a 5–10 line digest of this session with three sections — **Decided**,
> **Changed**, **Open** — one-line statements, each decision with a stable `CAL-*` ID, a date, and
> a reference key (or `[ref?]`), naming the files/modules touched. No filler.

```
Decided:
- CAL-<MODULE>-NN [date] <topic> … — [RefKey]
Changed:
- <ID> <what superseded a prior decision> — was: […]
Open:
- OQ-CAL-NN <question> → OPEN_QUESTIONS
```

## 3. Recalling context (search by content words)

Name the real topic; the §J index in `GLOSSARY.md` has ready-made phrases.
✅ "the union-of-damage rule and the shared-centroids requirement"
✅ "the timestep convergence anomaly — finer timestep lower losses"
❌ "that thing about the grid we discussed"

## 4. Reproducibility checklist (per run)

- [ ] Seed set once via `set_seed`; PyMC gets `random_seed=` derived from it (`CAL-GEN-04`).
- [ ] Manifest written (`RunManifest`) before results are read (`CAL-GEN-05`).
- [ ] Inputs frozen: hazards HDF5 + provenance verified; config resolved from `configs/` (`CAL-GEN-12`).
- [ ] Derived artifacts have a reconstructor script; nothing pickled (`CAL-GEN-03`).
- [ ] `environment.lock.yml` current if the env changed.
- [ ] Exact cross-machine replication needed? Pin BLAS threads (`OMP_NUM_THREADS=1`) and note it in the manifest.

## 5. Git

- Small descriptive commits; behaviour ≠ packaging/moves (`CAL-GEN-07`).
- Tags at milestones (`v0.1-hazards-frozen`, `v0.2-null-model`, `v0.3-jerarquico-viento`); traces
  and parameter tables are named by tag (`DC-CAL-BAYES-2`, `DC-CAL-OUT-1`).
- `data/`, `results/` ignored; canon and notes tracked.

---

## Related
[[00_README_CONTEXT]] · [[DECISIONS]] · Home: [[_INDEX]]
#arm/cal #type/workflow
