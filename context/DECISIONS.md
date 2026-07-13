# DECISIONS — impactcal-mx decision log

One line per decision. Format: `[ID] [date] decision — rationale. [RefKey | [eng]]`.
`[eng]` = engineering decision, no academic reference expected. `[ref?]` = reference to confirm
(see `OPEN_QUESTIONS.md`). Superseded decisions are **edited** in place, not appended. Reference
keys resolve in `REFERENCES.md`. ID scheme in `00_README_CONTEXT.md` §3.

> Decisions dated 2026-06-11 were taken in the design sessions and are recorded in full prose in
> the master design doc (`notes/theory/Calibracion_Impacto_Mexico_Master.md`, §2 D1–D13); this log
> is the canonical one-line index of them.

## Table of contents
- `CAL-GEN-*` — Cross-cutting standards (reproducibility, provenance, version control)
- `CAL-SCOPE-*` · `CAL-TARGET-*` · `CAL-XWALK-*` · `CAL-EXP-*`
- `CAL-WIND-*` · `CAL-SURGE-*` · `CAL-RAIN-*` · `CAL-RF-*`
- `CAL-IMPF-*` · `CAL-BAYES-*` · `CAL-MULTI-*` · `CAL-VAL-*` · `CAL-OUT-*`

---

## CAL-GEN — Cross-cutting standards

- `CAL-GEN-01` [2026-07-08] Every analytical/design decision carries a real, checkable reference, or is explicitly marked `[eng]`. No invented citations; unconfirmed refs go to `REFERENCES.md` §99. [standard]
- `CAL-GEN-02` [2026-07-08] Raw data is version-pinned with a provenance record per artifact (`_procedencia.json`: URL/dataset, sha256, bytes, date, + version/DOI/request where applicable), written/verified via `impactcal.infra.provenance`. Pipelines are **idempotent**: re-runs skip files verified intact unless `--forzar`. [eng]
- `CAL-GEN-03` [2026-07-08] Deterministic reconstructor scripts are the source of truth for any derived artifact; **never** pickled objects. The canonical calibration output is a parameter table + reconstructor (`CAL-OUT-01`). [eng]
- `CAL-GEN-04` [2026-07-08] All randomness routes through `impactcal.infra.set_seed`/`get_rng(stream)` (PCG64 via `np.random.default_rng` — bit-reproducible across OS/architectures); named streams are independent, so adding one never perturbs others. PyMC samplers receive `random_seed=` derived from the base seed. [eng]
- `CAL-GEN-05` [2026-07-08] Every stochastic/calibration run writes a manifest to `results/manifests/<run_id>.json` — resolved config + git commit (+dirty flag) + seed + package versions + timestamps (`impactcal.infra.RunManifest`). Cross-platform exact replication additionally requires pinned versions (`environment.lock.yml`) and single-threaded BLAS where float-sum order matters; documented in `infra/seeds.py`. [eng]
- `CAL-GEN-06` [2026-07-08] Configuration over hard-coding: parameters in `configs/calibracion.yaml`; all paths resolve via `impactcal.infra.ProjectPaths` (no CWD-relative paths); bulk data may live outside the repo via `IMPACTCAL_DATA_ROOT`. [eng]
- `CAL-GEN-07` [2026-07-08] Version control throughout: git from day one; small descriptive commits naming the module touched; **behaviour changes separate from packaging/move changes**; `data/` and `results/` git-ignored, `context/`, `notes/`, `literature/*.md` tracked. [eng]
- `CAL-GEN-08` [2026-07-08] Bilingual boundary: public Python APIs in English; Spanish data identifiers, CLI flags (`--forzar`, modos `verificar`/`descargar`/`calcular`), institution names, and peril labels kept **verbatim** (they are literal artifacts in the data). Canon documents in English with Spanish artifacts verbatim; the master theory doc stays in Spanish. [eng]
- `CAL-GEN-09` [2026-07-08] Repo is an Obsidian vault (wikilinks by basename, `## Related` footers, `#arm/cal` + `#type/*` tags, MOC hubs); conventions in `../OBSIDIAN_SETUP.md`. Diagrams in Mermaid, never ASCII box art; file trees stay plain code blocks. [eng]
- `CAL-GEN-10` [2026-07-08] Claude Code is the primary working interface; this canon is its memory. Root `CLAUDE.md` restates load-bearing rules and is read each session; auto memory is not relied upon for project decisions. Canon edits happen through the `/digest` (or `/compact-canon`) flow with the diff shown first. [eng]
- `CAL-GEN-11` [2026-07-08] Amounts held in **current MXN** at source; deflation to constant MXN via **INEGI INPC** is a documented downstream step (`CAL-TARGET-03`). [eng]
- `CAL-GEN-12` [2026-07-08] Calibration runs **only against frozen inputs**: hazards persisted to HDF5 with provenance, exposures and target tables versioned by hash. Nothing regenerates on the fly inside a calibration. [eng]
- `CAL-GEN-13` [2026-07-12] Development follows **YAGNI**: the minimal implementation that works — one-line solutions where possible; stdlib/native before custom code; no speculative abstractions, placeholder modules, or config without a present consumer. Complexity enters only when a concrete need pulls it in; audited periodically with `/ponytail-audit`. [eng]

## CAL-SCOPE — Alcance

- `CAL-SCOPE-01` [2026-06-11] Object: **state-level (32 entidades) impact functions for Mexico**, integrable to CLIMADA via per-point `impf_*` assignment; motivated by the bias of single regional functions (up to ×36 regionally). [Eberenz2021]
- `CAL-SCOPE-02` [2026-06-11] Perils in scope (fase 1): viento ciclónico, marejada (TCSurgeBathtub), lluvia ciclónica (TCRain), inundación fluvial (RiverFlood). **Pluvial/urban flooding out of scope**, declared limitation (CDMX/Monterrey/Guadalajara mechanism), CHIRPS/ERA5 precipitation→damage pilot as future work. [eng]
- `CAL-SCOPE-03` [2026-06-11] Hazard is **self-contained in CLIMADA** (TropCyclone wind fields, not the own IBTrACS/Holland pipeline): an impact function calibrated on one wind model is not transferable to another (`v_half` absorbs hazard bias), and downstream application happens in CLIMADA. Own-pipeline fields are therefore out for this branch. [Eberenz2021]

## CAL-TARGET — Pérdidas observadas y deflactación

- `CAL-TARGET-01` [2026-06-11] Two calibration routes: **(A) insured** — CNSF `MONTO PAGADO` losses vs CNSF sumas aseguradas exposure; **(B) total** — CENAPRED socioeconomic losses vs LitPop. B is the sensitivity check of A; two *independent* targets, internally consistent losses↔exposure per route. Motivated by low insurance penetration in Mexico. [Eberenz2021]
- `CAL-TARGET-02` [2026-06-11] Calibration unit: **año × estado** (not evento × estado) — CNSF is annual; multi-storm years make per-storm attribution ambiguous; analogous to EM-DAT overlap handling. Analysis period **2000–present**, bounded by the loss side (CENAPRED series), not by IBTrACS (~1980 satellite era). [Eberenz2021]
- `CAL-TARGET-03` [2026-06-11] Deflation to constant MXN with **INPC (INEGI)**, base year = last complete panel year. GDP deflators (WB/IMF) rejected for a domestic MXN series. USD conversion (Banxico FIX annual average) only for magnitude comparison with literature, never inside the calibration. [eng]
- `CAL-TARGET-04` [2026-07-12] CENAPRED interface = the **frozen consolidados of the climateCCR pipeline** (panel A, eventos B, multiestado, catálogo), copied into `data/cenapred/consolidados/` with sha256 + `_procedencia.json` sidecars recording the origin path (`impactcal.target.cenapred`, `impactcal.infra.freeze`); crudos + scraper stay upstream in climateCCR. Machine-readable coverage 2000–2015; extension 2016+ is `OQ-CAL-14`. [eng]

## CAL-XWALK — Crosswalk año-estado ↔ tormentas

- `CAL-XWALK-01` [2026-06-11] Affected set per year-state defined by modeled hazard: storms whose wind field intersects the state above `v_thresh`, **plus** states in the rain cone (TCRain above threshold) even without damaging wind — captures inland losses (e.g. CDMX) filed under inundación perils in CNSF. Annual observed loss compares against the modeled impact **aggregated over all storms of the year**; the observed loss is never partitioned across storms. Year-states with loss>0 but no modeled storm (and vice versa) are flagged for documented inclusion/exclusion. [eng]
- `CAL-XWALK-02` [2026-06-11] Peril-mapping rule for the target: a year-state's hydro loss is assigned to "ciclónica" if a storm reaches its rain cone that year, to "fluvial independiente" otherwise; mixed cases flagged. (Partition rule of the *target*, distinct from `CAL-XWALK-01` which defines the affected set.) [eng]
- `CAL-XWALK-03` [2026-07-12] Crosswalk **v0 is loss-side** (`impactcal.target.crosswalk`): CENAPRED CT events matched to IBTrACS SIDs by nombre+temporada (accents stripped, type-words dropped, numerales ES→EN), fallback = date-window overlap ±3 días among storms near Mexico (bbox 12–35°N, 84–120°W); event universe = subtipos ciclónicos {CT, MT, MF} + fluviales {LLUV, INUND}. Hazard-side affected set (`CAL-XWALK-01`) becomes **v1** once hazards freeze (`OQ-CAL-01`); `sids_cono_lluvia` stays empty in v0. Versioning: per-row `version_crosswalk`, scheme `v<major>.<minor>-<método>` (current `v0.1-nombres-fechas`). Real-run coverage: 165/167 CT events matched (82 nombre, 83 fechas). [eng]
- `CAL-XWALK-04` [2026-07-12] `familia_asignada` v0 uses the **matched-storm date window (±buffer) as documented proxy of the rain cone** (`CAL-XWALK-02`): LLUV/INUND year-state → `ciclonica` if all its events overlap a matched storm window of the year, `fluvial` if none, `mixta_flag` otherwise; reported CT presence → `ciclonica`. To be superseded by the TCRain cone in v1. [eng]

## CAL-EXP — Exposiciones

- `CAL-EXP-01` [2026-06-11] Ruta B exposure: `LitPop.from_countries(['MEX'])` — literature standard. [Eberenz2020LitPop]
- `CAL-EXP-02` [2026-06-11] Ruta A exposure: CNSF sumas aseguradas per state **of the event year** (temporal normalization for free), spatially disaggregated **∝ LitPop within each state** — documented assumption, sensitivity-checkable. [Eberenz2020LitPop]
- `CAL-EXP-03` [2026-06-11] Both `Exposures` carry `region_id` = clave INEGI (2-digit) via spatial join with the Marco Geoestadístico (pinned version), and `impf_TC`/`impf_TCSurgeBathtub`/`impf_TR`/`impf_RF` = state key. [eng]

## CAL-WIND / CAL-SURGE / CAL-RAIN / CAL-RF — Hazards

- `CAL-WIND-01` [2026-06-11] Wind hazard: `TCTracks.from_ibtracs_netcdf(provider='usa')`, basins EP+NA, ≥2000 → `equal_timestep` → `TropCyclone.from_tracks` on the exposure centroids. Historical tracks only for calibration. [Knapp2010][IBTrACSv04r01]
- `CAL-WIND-02` [2026-06-11; superseded 2026-07-12] Track interpolation timestep: **0.5 h, frozen** by the §3.4 convergence test (run `timestep_test_20260713T011309Z`; pipeline note [[timestep-convergence-test]]): at 1 h the **state grain does not converge** (Patricia 2015: Nayarit at 17% of the 0.25 h reference loss); at 0.5 h storm aggregates sit within ~6% and swath RMSE ≤ 2 m/s; the 0.25 h reference is stable vs 0.125 h. Anomaly resolved: coarse timesteps **undersample the per-cell max-wind swath** (loss falls monotonically with coarser Δt — the origin-project "finer→lower" sign was its 0.5° grid artifact, not timestep); timestep × centroid-resolution interaction negligible at 150–300 as. Frozen identical in calibration and every downstream application: residual consistent bias is absorbed into `v_half`. At hazard freeze: re-confirm 0.5 vs 0.25 h on the definitive grid + pin IBTrACS `.nc` provenance (`OQ-CAL-15`). [Eberenz2021][eng]
- `CAL-SURGE-01` [2026-06-11] Surge hazard: `TCSurgeBathtub.from_tc_winds(tc, topo_path)` — simplified Xu (2010) wind-surge relationship (pre-run SLOSH) with inland decay; DEM already in hand as `.tif` (provenance to record, `OQ-CAL-05`; standard reference SRTM15+ V2.0). [Xu2010][Tozer2019]
- `CAL-RAIN-01` [2026-06-11] Cyclonic-rain hazard: `TCRain` (climada-petals, `haz_type='TR'`, mm). Model choice R-CLIPER (default, cheaper) vs TCR pending a documented trial (`OQ-CAL-03`). [Tuleya2007][Lu2018]
- `CAL-RF-01` [2026-06-11] Fluvial hazard: `RiverFlood.from_nc(dph, frc)` from ISIMIP/CaMa-Flood NetCDF (in hand; exact simulation/GCM/GHM to record, `OQ-CAL-06`). Annual-maximum resolution → consistent with the año×estado unit (`CAL-TARGET-02`). GloFAS module (CDS discharge → return-period footprints) reserved as fase 2 refinement. [Sauer2021-ref?]
- `CAL-HAZ-SHARED-01` [2026-06-11] **All four hazards share the exposure centroids** — hard requirement for cell-level multi-peril combination (`CAL-MULTI-01`). Hazards frozen to HDF5 + `_procedencia.json` (CLIMADA version, IBTrACS version, generation params incl. timestep); calibration never regenerates them (`CAL-GEN-12`). [eng]

## CAL-IMPF — Formas funcionales

- `CAL-IMPF-01` [2026-06-11] Wind: Emanuel (2011) sigmoid via `ImpfTropCyclone.from_emanuel_usa` (the constructor implements the general functional form; "usa" only names its original defaults). **`v_thresh = 25.7 m/s` and `scale = 1` fixed; single free parameter `v_half` per state** — identifiability: freeing two shape parameters against aggregate losses yields flat cost valleys. Optional sensitivity `v_thresh ∈ {20, 25.7, 30}` on the national fit. [Emanuel2011][Eberenz2021]
- `CAL-IMPF-02` [2026-06-11] Surge & fluvial: JRC depth-damage shape (`ImpfRiverFlood.from_jrc_region_sector('NorthAmerica','residential')`) with a **state-level multiplicative MDD scalar** `κ_s` (clipped to [0,1] after scaling) as the only free parameter; separate `κ_s^surge` and `κ_s^RF` (salt vs fresh water mechanisms). [Huizinga2017]
- `CAL-IMPF-03` [2026-06-11] Cyclonic rain: preferred form is an Emanuel-type sigmoid on accumulated precipitation with fixed `P_thresh` and free `P_half,s`; fallback piecewise-linear scalar. Decided with data in hand; if not identifiable, collapses to the null model and is reported (`OQ-CAL-04`). [eng]

## CAL-BAYES — Modelo jerárquico y superficies

- `CAL-BAYES-01` [2026-06-11] Sparse events per state → **hierarchical Bayesian partial pooling** (state detail preserved; coast-less states shrink to a regional/national mean with direct physical interpretation). `climada.util.calibrate` `BayesianOptimizer` is Bayesian *optimization* (GP search → point optimum), **not** inference — used only for the national null fit and diagnostics; inference in PyMC (optional Stan replication). [GelmanHill2007][Eberenz2021]
- `CAL-BAYES-02` [2026-06-11] CLIMADA enters as a **precomputed surface** (exact surrogate): for frozen hazard+exposure, per-state-year loss is monotone in the single free parameter → tabulate `L_st(v_half)` on a grid (30–120 m/s, step 2) and `L_st(κ)` (0.1–3.0, step 0.1); the PyMC likelihood interpolates (monotone PCHIP), never calls CLIMADA. Export: `(estado, año, malla)` tensors in parquet/NetCDF with provenance. Joint multi-peril surface on a coarse `(v_half, κ_surge, κ_rain)` grid, refined after an exploratory run. [eng]
- `CAL-BAYES-03` [2026-06-11] Specification: `log V_half,s ~ N(μ_g(s), τ²)` with regional groups g (Pacífico Sur / Pacífico Norte-BC / Golfo / Yucatán / Interior, grouping justified by track climatology); hyperprior `μ_g` anchored to the Eberenz NA regional `V_half` **as prior, not data**; `log κ_s ~ N(0, σ²)` centered on the JRC curve; lognormal likelihood on losses (MSLE/RMSF spirit — losses span orders of magnitude). Zeros/deductible censoring: hurdle/left-censoring, finalized with data (`OQ-CAL-07`). [GelmanHill2007][Eberenz2021]

## CAL-MULTI — Agregación multi-peril

- `CAL-MULTI-01` [2026-06-11] Combination at **cell level** with the union-of-damage rule `f_total = 1 − (1−f_viento)(1−f_marejada)(1−f_lluvia)` (HAZUS combined wind-flood logic): bounded by asset value, no double counting by construction; direct summation systematically overestimates on the coast. Implicit conditional-independence assumption documented; conservative alternative `max(f_i)` as lower bound in sensitivity. Post-processing over the three `imp_mat` on shared centroids. [Hazus-ref?]
- `CAL-MULTI-02` [2026-06-11] **One likelihood against total observed loss** with the three parameter blocks inside — zero double counting. Partition identified via (i) asymmetric priors (water curves anchored to JRC, only scale free; the truly free parameter is `v_half`) and (ii) physical event signatures (wind-dominated vs rain-dominated storms in the panel). Posterior cross-block correlations reported as identifiability diagnostic; if unidentified, collapse to null model and report. [Huizinga2017][Eberenz2021]

## CAL-VAL — Validación

- `CAL-VAL-01` [2026-06-11] Validation set: (1) leave-one-year-out on major-event years; (2) external benchmark — national/regional posterior vs Eberenz NA `V_half` (the headline result is the subnational heterogeneity the regional mean hides); (3) ruta A vs ruta B state-vulnerability rankings; (4) **null model** = pure Eberenz scheme (wind-only vs total, `v_half` implicitly absorbing surge+rain) — if the 3-sub-peril decomposition doesn't beat it out-of-sample, that is reported as a result; (5) MCMC diagnostics (R-hat, ESS, divergences) via ArviZ. [Eberenz2021]

## CAL-OUT — Exportación

- `CAL-OUT-01` [2026-06-11] Canonical artifact: `parametros_impacto_estatal.csv` (git-versioned; columns per `DC-CAL-OUT-1`) + deterministic reconstructor `construir_impfset.py`. Downstream (incl. climateCCR) consumes **the table**, never serialized objects. Posterior traces as ArviZ NetCDF named by git tag; precomputed surfaces in parquet/NetCDF with provenance; per-run decision log (which year-states entered the likelihood, crosswalk version, delta vs previous run). [eng]

---

## Related
[[00_README_CONTEXT]] · [[DATA_CONTRACTS]] · [[REFERENCES]] · [[OPEN_QUESTIONS]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/decisions
