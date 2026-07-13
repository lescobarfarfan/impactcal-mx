# OPEN_QUESTIONS — impactcal-mx

Only what is genuinely open. When resolved: move to `DECISIONS.md` (dated), delete here.
IDs `OQ-CAL-NN`; gating items first.

## Gating (block the next deliverable)

- `OQ-CAL-01` **Timestep convergence test** (`CAL-WIND-02`; protocol in master doc §3.4). Includes explaining the observed finer-timestep → lower-losses effect (check the timestep × centroid-resolution interaction; cf. the CDMX 0.5° discretization artifact in the origin project). Hazards cannot be frozen until this closes.
- `OQ-CAL-02` **Crosswalk v1 (hazard-side)** (`CAL-XWALK-01`; v0 delivered, `CAL-XWALK-03/04`): rain-cone intensity threshold (TCRain); wind-field verification of the v0 affected set (loss>0/no storm, storm/no loss); resolution of the v0 review queue — 220 `mixta_flag` year-states, 68 date-matches with multiple SID candidates, 2 `sin_match` events of 2000; optional fuzzy name matching (CENAPRED typos, e.g. "Julette"). **Blocked on `OQ-CAL-01`** (needs frozen hazards).

## Modelling

- `OQ-CAL-03` **TCRain model choice** — R-CLIPER vs TCR: run both on 2–3 major events, compare footprints vs reported rainfall, document (`CAL-RAIN-01`).
- `OQ-CAL-04` **Rain damage-function form + identifiability** (`CAL-IMPF-03`): fix `P_thresh` (percentile of no-loss events?); does the rain block identify at all, or collapse to null model?
- `OQ-CAL-07` **Zeros / deductible censoring** in the likelihood (`CAL-BAYES-03`): hurdle vs left-censoring; ruta A deductible floor per line of business?
- `OQ-CAL-09` **Regional grouping g(s)** for hyperpriors (`CAL-BAYES-03`): confirm the 5-group proposal (Pacífico Sur / Pacífico Norte-BC / Golfo / Yucatán / Interior) against track climatology; document assignment table.
- `OQ-CAL-10` **Joint multi-peril surface** (`CAL-BAYES-02`): coarse-grid resolution for `(v_half, κ_surge, κ_rain)`; refinement strategy after the exploratory run.

## Data & provenance

- `OQ-CAL-05` **DEM provenance**: identify the in-hand elevation `.tif` (SRTM15+ V2.0? resolution? processing?) and write its `_procedencia.json` before `CAL-SURGE-01` runs.
- `OQ-CAL-06` **ISIMIP flood files provenance**: exact simulation round, GHM, GCM forcing, scenario of the in-hand depth/fraction `.nc`; write provenance (`CAL-RF-01`).
- `OQ-CAL-11` **CNSF sums-insured availability**: confirm sumas aseguradas per state-year are extractable at the needed grain from the existing pipeline (`DC-CAL-TARGET-3`); else define ruta A exposure fallback.
- `OQ-CAL-14` **CENAPRED panel 2016–2023**: the frozen machine-readable series ends in 2015 (`CAL-TARGET-04`); the structured captures of the extenso PDFs (protocol in climateCCR `cenapred.md` §6bis, PDFs already in hand) must be done upstream and re-ingested to cover the full `CAL-TARGET-02` period; 2024 = only real gap (extenso unpublished).

## References (§99)

- `OQ-CAL-08` Verify before manuscript: `[Xu2010]` exact venue; `[Sauer2021-ref?]` DOI/title; `[Hazus-ref?]` current edition; `[Wagenaar2018-ref?]` journal. (`REFERENCES.md` §99.)

## Housekeeping / integration

- `OQ-CAL-12` **Merge decision with `climateCCR`**: fold into `calibration/impact/` (per climateCCR `INT-05`) vs stay a sibling repo consumed via `DC-CAL-OUT-1`. Decide once the null-model calibration runs end-to-end. Merge discipline pre-agreed in `00_README_CONTEXT.md` §0.
- `OQ-CAL-13` **Package/repo name** — `impactcal` / `impactcal-mx` is provisional; check PyPI/GitHub availability before publishing anything (precedent: climateCCR's `climrisk` rename was rejected for a name collision).

---

## Related
[[DECISIONS]] · [[REFERENCES]] · Home: [[_INDEX]]
#arm/cal #type/open-questions
