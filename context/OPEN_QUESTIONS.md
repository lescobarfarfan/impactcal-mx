# OPEN_QUESTIONS — impactcal-mx

Only what is genuinely open. When resolved: move to `DECISIONS.md` (dated), delete here.
IDs `OQ-CAL-NN`; gating items first.

## Gating (block the next deliverable)

- `OQ-CAL-19` **Deflactación INPC: ruta de obtención y año base** (`CAL-TARGET-03`, `DC-CONV-4`). El objetivo ruta B ya existe (`DC-CAL-TARGET-2`, 750 filas 2000–2023) pero **en MXN corrientes**; sin la columna `monto_total_mxn_{base}` no hay calibración defendible entre años (el panel abarca 24 años y el nivel de precios se multiplica ~2.8× entre 2000 y 2023). El índice está decidido — INPC de INEGI — pero **no la ruta de obtención**: la API BIE de INEGI exige token, y el relevo del Banco Mundial (`FP.CPI.TOTL`, MEX, base 2010=100) sí es accesible sin token y tiene al INPC como fuente subyacente pero **no es la cita que `CAL-TARGET-03` nombra** (`CAL-GEN-01`). Decidir: (a) archivo/API directo de INEGI con procedencia propia, o (b) relevo del Banco Mundial documentado como tal. Fijar además `deflactor.anio_base` — el último año completo del panel es ahora **2023**. Bloquea los pasos 5+ de la secuencia (modelo nulo → superficies → PyMC).

## Modelling

- `OQ-CAL-03` **TCRain model choice** — R-CLIPER vs TCR: run both on 2–3 major events, compare footprints vs reported rainfall, document (`CAL-RAIN-01`).
- `OQ-CAL-04` **Rain damage-function form + identifiability** (`CAL-IMPF-03`): fix `P_thresh` (percentile of no-loss events?); does the rain block identify at all, or collapse to null model?
- `OQ-CAL-07` **Zeros / deductible censoring** in the likelihood (`CAL-BAYES-03`): hurdle vs left-censoring; ruta A deductible floor per line of business?
- `OQ-CAL-09` **Regional grouping g(s)** for hyperpriors (`CAL-BAYES-03`): confirm the 5-group proposal (Pacífico Sur / Pacífico Norte-BC / Golfo / Yucatán / Interior) against track climatology; document assignment table.
- `OQ-CAL-10` **Joint multi-peril surface** (`CAL-BAYES-02`): coarse-grid resolution for `(v_half, κ_surge, κ_rain)`; refinement strategy after the exploratory run.
- `OQ-CAL-16` **RF protection level** (`CAL-RF-04`): `none` vs `flopros` in the likelihood. Ahora se decide **una sola vez**, sobre el único bloque fluvial (GloFAS 2000–2023); ambas variantes están congeladas como hazards (`haz_rf_glofas_{none,flopros}.h5`, 8,594 vs 7,752 centroides con agua — la protección recorta ~10%). Decidir con datos; flopros = estándares reales de protección, pero groseros para México (`[Scussolini2016-ref?]`). Los artefactos ISIMIP2a conservan las dos variantes por simetría, para el contraste de `CAL-VAL-01`.

## Data & provenance

- `OQ-CAL-11` **CNSF sums-insured availability**: confirm sumas aseguradas per state-year are extractable at the needed grain from the existing pipeline (`DC-CAL-TARGET-3`); else define ruta A exposure fallback. **Cleaning prerequisite (2026-07-18, `CAL-GEN-14` run): partially resolved same day for the ramo agrícola** — the ×1000 cluster **and** a second systemic mode (`SUMA ASEGURADA` ≈×FIX 2022–2024) are now corrected upstream in climateCCR (`CAL-TARGET-05`; 915 renglones, copias `*_corregida.csv`, 132 firma-débil pendientes de revisión manual). **Remaining before any ruta A use**: run the same gate on the **ramo hidro** consolidados (riesgos_hidrometereologicos — both error modes could recur there) + the label-normalization rule (`limpieza_cnsf.clasificar_entidad` exists upstream; year-block case variants `SINALOA` vs `Sinaloa` split groupbys silently).
- `OQ-CAL-14` **CENAPRED 2024** (resto cerrado 2026-07-23 por `CAL-TARGET-06`: 2016–2023 capturados, validados e ingeridos). Queda sólo 2024: el extenso no se ha publicado, el resumen ejecutivo da 6 filas en alcance sobre 5 estados y ningún estado fluvial con daño, así que el año está **fuera del panel** (`periodo.anio_final: 2023`). Al publicarse el extenso: re-capturar, re-ingerir, mover `anio_final` a 2024 y re-correr crosswalk + tabla objetivo.
- `OQ-CAL-18` **Marco Geoestadístico edition** (`CAL-EXP-04`, `DC-CONV-5`): the local `00ent` shapefile carries no version metadata — identify the INEGI MG edition (year) and record it in the frozen provenance.

## References (§99)

- `OQ-CAL-08` Verify before manuscript: `[Xu2010]` exact venue; `[Sauer2021-ref?]` DOI/title; `[Hazus-ref?]` current edition; `[Wagenaar2018-ref?]` journal; `[Dottori2016-ref?]` exact citation of the JRC flood hazard maps; `[Scussolini2016-ref?]` authors/pages; `[GumbelGloFAS-ref?]` dataset authors/DOI; `[Leys2013-ref?]` DOI/pages (MAD robust z, `CAL-GEN-14`). (`REFERENCES.md` §99.)

## Housekeeping / integration

- `OQ-CAL-12` **Merge decision with `climateCCR`**: fold into `calibration/impact/` (per climateCCR `INT-05`) vs stay a sibling repo consumed via `DC-CAL-OUT-1`. Decide once the null-model calibration runs end-to-end. Merge discipline pre-agreed in `00_README_CONTEXT.md` §0.
- `OQ-CAL-13` **Package/repo name** — `impactcal` / `impactcal-mx` is provisional; check PyPI/GitHub availability before publishing anything (precedent: climateCCR's `climrisk` rename was rejected for a name collision).

---

## Related
[[DECISIONS]] · [[REFERENCES]] · Home: [[_INDEX]]
#arm/cal #type/open-questions
