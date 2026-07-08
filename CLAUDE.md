# impactcal-mx — Claude Code project instructions

impactcal-mx calibrates **subnational (state-level) CLIMADA impact functions for Mexico** —
hydrometeorological perils only: ciclón (viento + marejada + lluvia) and inundación fluvial —
against two loss targets (ruta A: CNSF insured; ruta B: CENAPRED total), via a **hierarchical
Bayesian (partial-pooling) model in PyMC over precomputed CLIMADA loss surfaces**. The canonical
deliverable is `parametros_impacto_estatal.csv` + its deterministic reconstructor
(`construir_impfset.py`).

This is a **standalone working branch** related to the `climateCCR` thesis repo (merge decision
open, `OQ-CAL-12`; merge discipline pre-agreed in `context/00_README_CONTEXT.md` §0).

## The context canon (authoritative — read before deciding)

The single source of truth lives in `context/`:

| File | Holds |
|---|---|
| `context/00_README_CONTEXT.md` | Entry point, module map, `CAL-*` ID scheme, maintenance rules. |
| `context/DECISIONS.md` | Every decision, one line, stable ID, date, reference key. |
| `context/DATA_CONTRACTS.md` | I/O specs: names, grain, columns, units, crosswalks. |
| `context/GLOSSARY.md` | Terms + content-word retrieval index (§J). |
| `context/REFERENCES.md` | Verified bibliography; §99 = to-confirm. |
| `context/OPEN_QUESTIONS.md` | Open items; gating questions first. |
| `context/WORKFLOW.md` | Working discipline + end-of-session ritual. |

The full-prose design (formulas, rationale, flow) is
`notes/theory/Calibracion_Impacto_Mexico_Master.md` — the canon indexes it.

**Before working on or deciding anything, read the relevant `context/` file(s).** The canon is
authoritative: if anything you recall conflicts with it, the canon wins. Never contradict a logged
decision without flagging it and proposing a supersede.

## This repo is also an Obsidian vault

`context/`, `notes/`, `literature/`, and the root hubs (`_INDEX.md`, `CAL_MOC.md`) form an
Obsidian vault. Conventions: `OBSIDIAN_SETUP.md`. When editing/creating notes, **maintain the
graph**: wikilinks by basename (`[[DECISIONS]]`, `[[CAL_MOC]]`); every note ends with a
`## Related` footer + `#arm/cal` and `#type/<…>` tags; new `notes/*` notes get linked from
`[[CAL_MOC]]`; vault notes are one paragraph = one source line, math in LaTeX (`$…$`).

## Non-negotiable rules

- **One source of truth per fact.** Supersede by editing the canonical entry in place; never
  append a second live version.
- **Every analytical/modelling decision carries a real, checkable reference** from
  `context/REFERENCES.md`, or is marked `[eng]`. Never invent a citation; unconfirmed →
  `REFERENCES.md` §99 (`CAL-GEN-01`).
- **Reproducibility (`CAL-GEN-*`):** randomness only through `impactcal.infra.set_seed`/`get_rng`
  (seed recorded); every stochastic/calibration run writes `results/manifests/<run_id>.json`;
  derived artifacts come from deterministic reconstructor scripts, **never pickles**; pipelines
  idempotent (`--forzar`); params in `configs/calibracion.yaml`, paths via
  `impactcal.infra.ProjectPaths`; amounts in current MXN, INPC deflation downstream.
- **Calibration only runs against frozen inputs** (`CAL-GEN-12`): hazards from HDF5 + verified
  `_procedencia.json`; never regenerate hazards inside a calibration.
- **Bilingual boundary (`CAL-GEN-08`):** public Python APIs in English; Spanish data identifiers,
  CLI flags, institution and peril names kept **verbatim**.
- **Diagrams in Mermaid**, never ASCII box art; file trees stay plain code blocks.
- **Scope:** hydrometeorological perils only; pluvial/urban flooding explicitly out (declared
  limitation, `CAL-SCOPE-02`); geophysical perils out.
- **ID scheme:** `CAL-<MODULE>-NN` (see `context/00_README_CONTEXT.md` §3).

## Code standards

- Python: PEP 8 + Google Python Style Guide; type hints on public APIs.
- `ruff` (E/F/I/UP/B, `--fix`) + `black` (line length 100); both clean before commit.
- Tests: `pytest` units per module; the infra layer stays green (`tests/test_infra.py`); each new
  pipeline gets ≥1 end-to-end test on a tiny fixture.
- Version control: small descriptive commits naming the module; behaviour changes separate from
  packaging/moves.

### Common commands
```bash
conda env create -f environment.yml && conda activate impactcal   # first time
pip install -e ".[dev]"                                           # if not via conda pip section
pytest                     # test suite
ruff check . && black .    # lint + format
pre-commit install         # enable hooks
```

## Session workflow (manual commands + nudges)

Project slash commands (`.claude/commands/`): **`/warmstart`** (start of session — project-state
recap from the canon) · **`/digest`** (end of session — Decided/Changed/Open → writes the canon +
read-log + commits) · **`/link-check`** (vault audit) · **`/new-note`** (scaffold a linked note) ·
**`/compact-canon`** (periodic dedup).

Because these are manual and I am forgetful:

- **At the start of a session, if I have not run `/warmstart`, remind me to.**
- **When I signal wrap-up — or after any substantive decision — offer `/digest`.** If notes were
  added/moved, also offer `/link-check`.
- **Never edit `context/` files outside the `/digest` (or `/compact-canon`) flow without showing
  me the diff first.**

## Memory

The version-controlled canon in `context/` is the single source of truth — do not rely on auto
memory for project decisions.
