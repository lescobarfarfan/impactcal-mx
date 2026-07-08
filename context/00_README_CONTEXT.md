# 00 · README — impactcal-mx project context

**Project:** `impactcal-mx` — subnational (state-level) **CLIMADA impact-function calibration for
Mexico**, hydrometeorological perils: ciclón (viento, marejada, lluvia) + inundación fluvial.
Calibrated against CNSF insured losses (ruta A) and CENAPRED total losses (ruta B), via a
hierarchical Bayesian (partial-pooling) model over precomputed CLIMADA loss surfaces.

**Seeded:** 2026-07-08, from the design sessions of the `Climate-Nature-Risks_Calibration` /
calibration branch (master design doc: `notes/theory/[[Calibracion_Impacto_Mexico_Master]]`).

---

## 0. Relationship to `climateCCR` (read this first)

This repo is a **deliberately standalone working branch**. The consolidated thesis project
(`climateCCR`, three arms CCR/MKT/HAZ) tracks this work at a summary level under its
`HAZ-CLIMADA-*` IDs; whether this branch's outputs merge into that repo (as
`calibration/impact/`, per climateCCR `INT-05`) or remain a sibling repo consumed via its
canonical parameter table is **open** (`OQ-CAL-12`).

**Merge discipline (decided now, so a future merge is mechanical):**
- IDs here use the **`CAL` arm prefix** (`CAL-<MODULE>-NN`). On integration, each `CAL-*` entry is
  imported into the climateCCR canon under `HAZ-CLIMADA-*` (or kept verbatim with a crosswalk
  line); never re-derived from memory.
- The **consumption interface is the canonical parameter table** (`DC-CAL-OUT-1`), not code or
  pickles — climateCCR can already consume it today without any merge.
- The reproducibility standard (`CAL-GEN-*`) mirrors climateCCR's `GEN-*` one-for-one, so nothing
  needs re-litigating at merge time.

## 1. What this is

The `context/` folder is the **single source of truth** for this project's decisions, contracts,
vocabulary, references, open items, and workflow. Living documents: edit in place, never
accumulate duplicates. Code is not consolidated here — `src/impactcal/` is its own source of
truth; theory lives in `notes/theory/`; papers in `literature/`.

**Cross-cutting standards (non-negotiable):** every analytical decision carries a real, checkable
reference or is marked `[eng]`; raw data is version-pinned with `_procedencia.json`; pipelines are
reproducible, idempotent, deterministic (reconstructor scripts, never pickles); every stochastic or
calibration run writes a manifest (config + git commit + seed + versions); all randomness routes
through `impactcal.infra.set_seed`/`get_rng`; all work under git.

## 2. Document map

| Document | Purpose |
|---|---|
| `00_README_CONTEXT.md` | This file. Entry point + module map + ID scheme + maintenance rules. |
| `DECISIONS.md` | Dated log, one line per decision, stable ID, reference key. |
| `DATA_CONTRACTS.md` | I/O specs: names, grain, columns, units, conventions, crosswalks. |
| `GLOSSARY.md` | Terms + content-word retrieval index. |
| `REFERENCES.md` | Verified bibliography; §99 = to-confirm. |
| `OPEN_QUESTIONS.md` | Open items; gating questions first. |
| `WORKFLOW.md` | Working discipline + end-of-session ritual. |

Companion docs one level up (about the **repository**, not the intellectual content):
`../README.md` (project map), `../REPO_STRUCTURE.md` (layout), `../OBSIDIAN_SETUP.md` (vault
conventions), `../CLAUDE.md` (Claude Code instructions).

## 3. ID scheme

Single arm: **`CAL`**. Cross-cutting standards: **`CAL-GEN-*`**.

- **Decisions** — `CAL-<MODULE>-NN`. Modules:
  `SCOPE` (alcance) · `TARGET` (tablas de pérdidas y deflactación) · `XWALK` (crosswalk
  año-estado↔tormentas) · `EXP` (exposiciones) · `WIND` (hazard viento) · `SURGE` (marejada) ·
  `RAIN` (lluvia ciclónica) · `RF` (inundación fluvial) · `IMPF` (formas funcionales) ·
  `BAYES` (modelo jerárquico y superficies) · `MULTI` (agregación multi-peril) ·
  `VAL` (validación) · `OUT` (exportación/artefactos canónicos).
- **Data contracts** — `DC-CAL-<MODULE>-N`; conventions `DC-CONV-*`; joins `DC-XWALK-*`.
- **Open questions** — `OQ-CAL-NN` (gating first).
- **References** — citation keys `[Eberenz2021]`, `[Huizinga2017]`, … defined in `REFERENCES.md`.

Example cross-reference: "`CAL-IMPF-01` is backed by `[Emanuel2011]` + `[Eberenz2021]`; its output
contract is `DC-CAL-OUT-1`; the surface it feeds is `CAL-BAYES-02`."

## 4. Maintenance rules

**(a) Promote, don't duplicate.** A superseding decision **edits** the canonical entry in place
(or marks `→ SUPERSEDED by [date]` only if history is load-bearing). One source of truth per fact.

**(b) End-of-session ritual.** Before closing any working session: digest (Decided/Changed/Open) →
fold into `DECISIONS.md` → update contracts/glossary/references/open items → session read-log →
commit. Template in `WORKFLOW.md`.

**(c) Search by content words.** Name the real topic ("the timestep convergence test", "the
union-of-damage rule", "the sumas-aseguradas LitPop disaggregation") — not meta-words. Index at the
end of `GLOSSARY.md`.

**(d) Every analytical decision carries a reference** from `REFERENCES.md`, or is marked `[eng]`.
Never invent a citation; unconfirmed → `REFERENCES.md` §99.

**(e) Compact periodically** (`/compact-canon`): dedupe, reorganize, update "Last compaction".

**(f) One project.** This branch's chats live in one claude.ai project / one repo. If work must
happen elsewhere, run the ritual there and merge by hand into this canon.

---

## Related
[[_INDEX]] · [[DECISIONS]] · [[DATA_CONTRACTS]] · [[GLOSSARY]] · [[REFERENCES]] · [[OPEN_QUESTIONS]] · [[WORKFLOW]] · [[CAL_MOC]] · [[Calibracion_Impacto_Mexico_Master]]
#arm/cal #type/workflow
