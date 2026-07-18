# OPEN_QUESTIONS — impactcal-mx

Only what is genuinely open. When resolved: move to `DECISIONS.md` (dated), delete here.
IDs `OQ-CAL-NN`; gating items first.

## Gating (block the next deliverable)

- *(ninguna actualmente — `OQ-CAL-02` closed 2026-07-14: crosswalk v1 delivered, `CAL-XWALK-03/04`; the residual review queues live as `DC-XWALK-1` flags and are consumed by the per-run decision log, `CAL-OUT-01`.)*

## Modelling

- `OQ-CAL-03` **TCRain model choice** — R-CLIPER vs TCR: run both on 2–3 major events, compare footprints vs reported rainfall, document (`CAL-RAIN-01`).
- `OQ-CAL-04` **Rain damage-function form + identifiability** (`CAL-IMPF-03`): fix `P_thresh` (percentile of no-loss events?); does the rain block identify at all, or collapse to null model?
- `OQ-CAL-07` **Zeros / deductible censoring** in the likelihood (`CAL-BAYES-03`): hurdle vs left-censoring; ruta A deductible floor per line of business?
- `OQ-CAL-09` **Regional grouping g(s)** for hyperpriors (`CAL-BAYES-03`): confirm the 5-group proposal (Pacífico Sur / Pacífico Norte-BC / Golfo / Yucatán / Interior) against track climatology; document assignment table.
- `OQ-CAL-10` **Joint multi-peril surface** (`CAL-BAYES-02`): coarse-grid resolution for `(v_half, κ_surge, κ_rain)`; refinement strategy after the exploratory run.
- `OQ-CAL-16` **RF protection level** (`CAL-RF-02`): `none` vs `flopros` in the likelihood — both variants frozen, now also as hazards (`haz_rf_{none,flopros}.h5`); decide with data (flopros = real protection standards, but coarse for Mexico; the equivalent choice exists in `rf_glofas` output, so it applies uniformly to both segments).
- `OQ-CAL-17` **GloFAS footprint pipeline + segment consistency** (`CAL-RF-03`): every input is frozen (crudos 2011–2015; static aux 2026-07-16: `flood-maps.nc`, `gumbel-fit.nc`, FLOPROS). Remaining: (a) compute the 2011–2015 footprints with petals `rf_glofas` (daily discharge → annual max → Gumbel return period → JRC map interpolation → protección `none`/`flopros`) on the shared centroids; (b) consistency check vs ISIMIP2a on overlap years (both methodologies coexist 1979–2010) **before** mixing segments in one likelihood; (c) Gumbel-fit edition: frozen 1979–2015 (hdl:20.500.11850/641667, the one petals references) vs 1979–2023 (hdl:20.500.11850/726304) — decide by consistency with the GloFAS-ERA5 **v4.0** discharge.

## Data & provenance

- `OQ-CAL-11` **CNSF sums-insured availability**: confirm sumas aseguradas per state-year are extractable at the needed grain from the existing pipeline (`DC-CAL-TARGET-3`); else define ruta A exposure fallback. **Cleaning prerequisite (2026-07-18, `CAL-GEN-14` run): partially resolved same day for the ramo agrícola** — the ×1000 cluster **and** a second systemic mode (`SUMA ASEGURADA` ≈×FIX 2022–2024) are now corrected upstream in climateCCR (`CAL-TARGET-05`; 915 renglones, copias `*_corregida.csv`, 132 firma-débil pendientes de revisión manual). **Remaining before any ruta A use**: run the same gate on the **ramo hidro** consolidados (riesgos_hidrometereologicos — both error modes could recur there) + the label-normalization rule (`limpieza_cnsf.clasificar_entidad` exists upstream; year-block case variants `SINALOA` vs `Sinaloa` split groupbys silently).
- `OQ-CAL-14` **CENAPRED panel 2016–2023**: the frozen machine-readable series ends in 2015 (`CAL-TARGET-04`); the structured captures of the extenso PDFs (protocol in climateCCR `cenapred.md` §6bis, PDFs already in hand) must be done upstream and re-ingested to cover the full `CAL-TARGET-02` period; 2024 = only real gap (extenso unpublished).
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
