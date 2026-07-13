# Read-log — 2026-07-12 — YAGNI canon + ponytail audit

Session deliverables: `CAL-GEN-13` (YAGNI discipline, folded into [[DECISIONS]] + `CLAUDE.md`) and a whole-repo over-engineering audit — 4 cuts applied (`crosswalk.py`, `paths.py`, `pyproject.toml`), 4 findings kept by explicit decision. All decisions `[eng]`; the background sources below are engineering literature, deliberately **not** added to [[REFERENCES]] (`CAL-GEN-01` exempts `[eng]`).

**Fowler, "Yagni" (martinfowler.com bliki, 2015) + Beck, *Extreme Programming Explained* (origin of the term) `[eng, informal]`** — backs `CAL-GEN-13`: the cost of a presumptive feature is carry (build + maintain + obscure) paid now against a need that may never arrive, versus a usually similar build cost paid later with better information; that asymmetry is the rationale for "complexity enters only when a concrete need pulls it in".

**pandas user guide, `DataFrame` construction from a list of dicts (insertion-order columns)** — backs the `_COLUMNAS_XWALK` cut in `impactcal.target.crosswalk`: the row dicts are single literals, so column order is already deterministic without `columns=`; worse, `columns=` on a renamed key silently emits an all-NaN column instead of failing — the guard was a liability, not a safety net.

**`CAL-GEN-04` + `tests/test_infra.py`** — backs keeping `seeds.py` despite zero production callers today: canon-mandated, tested, and the PyMC layer (`CAL-BAYES-01/03`) is its intended consumer; strict-YAGNI deletion was considered and rejected 2026-07-12 as contradicting a logged decision only to rewrite the module weeks later.

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[GLOSSARY]] · Home: [[_INDEX]]
#arm/cal #type/reading
