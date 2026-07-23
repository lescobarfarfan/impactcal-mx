# DATA_CONTRACTS — impactcal-mx

What each module produces and consumes: name, grain, key columns, units, source of truth.
If a contract changes, **edit it here** and log it in `DECISIONS.md`. IDs: `DC-CAL-<MODULE>-N`;
conventions `DC-CONV-*`; joins `DC-XWALK-*`.

**Status tags:** `FIRM` (decided) · `PROPOSED` (default, confirm) · `TBD`.

---

## DC-CONV — Conventions

- `DC-CONV-1` Layout: installable `src/impactcal/` package; data under `data/<fuente>/{crudos,consolidados}`; heavy data optionally outside the repo via `IMPACTCAL_DATA_ROOT` (`CAL-GEN-06`). `FIRM`
- `DC-CONV-2` Provenance: every raw artifact carries `<file>._procedencia.json` (URL/dataset, sha256, bytes, date, version/DOI) via `impactcal.infra.provenance`. `FIRM`
- `DC-CONV-3` Run manifests: `results/manifests/<run_id>.json` (config + git commit + seed + versions + timestamps). `FIRM`
- `DC-CONV-4` Currency: current MXN at source; INPC deflation downstream (`CAL-TARGET-03`); constant-MXN columns suffixed `_mxn_{anio_base}`. `FIRM`
- `DC-CONV-5` Geography: 32 entidades; key = **clave INEGI 2-digit, zero-padded string** (`"01"`–`"32"`), column `cve_ent`. Marco Geoestadístico shapefile pinned with provenance. `FIRM`
- `DC-CONV-6` Encoding: canonical outputs UTF-8 CSV; `.xlsx` views disposable, never source of truth. `FIRM`

## DC-CAL-TARGET — Loss tables

- `DC-CAL-TARGET-1` **Ruta A (insured):** `perdidas_aseguradas_anual.csv` — grain año×estado×familia_peril; columns `anio, cve_ent, familia_peril {ciclonica|fluvial}, monto_pagado_mxn_corr, monto_pagado_mxn_{base}, n_registros`. Source: CNSF pipeline (`MONTO PAGADO`). `PROPOSED` (schema; confirm against pipeline output)
- `DC-CAL-TARGET-2` **Ruta B (total):** `perdidas_totales_anual.csv` — grain año×estado×familia_peril; columns `anio, cve_ent, familia_peril {ciclonica|fluvial}, monto_total_mxn_corr, n_eventos, defunciones, fuente_publicacion, familia_xwalk, flag_revision, version_crosswalk`. **Delivered 2026-07-23** (`impactcal.target.perdidas`, `data/target/`): 750 filas, 2000–2023, 32 estados, desde los consolidados congelados (`CAL-TARGET-04/06`). `familia_peril` es lo que **reporta** CENAPRED (Ciclón tropical + Marejada → ciclonica; Daños por lluvia + Inundación → fluvial); la regla de atribución de `CAL-XWALK-02` viaja aparte en `familia_xwalk` para que la máscara de inclusión (`DC-CAL-TARGET-4`) no re-derive nada. `fuente_publicacion` distingue `base_abierta_2000_2015` / `extenso_{año}` / `resumen_{año}`. Montos en **MXN corrientes**; la columna deflactada `monto_total_mxn_{base}` falta hasta resolver `OQ-CAL-19`. `FIRM`
- `DC-CAL-TARGET-3` **Sumas aseguradas:** `sumas_aseguradas_anual.csv` — grain año×estado; `anio, cve_ent, suma_asegurada_mxn_corr`. `PROPOSED`
- `DC-CAL-TARGET-4` **Calibration matrix** (what `calibrate`/`bayes` consume): wide DataFrame rows=`anio`, columns=`cve_ent`, values=loss in constant MXN; one per (ruta, familia_peril); accompanied by an inclusion-mask matrix from `DC-XWALK-1` flags. `FIRM` (shape required by `climada.util.calibrate`)

## DC-XWALK — Crosswalk

- `DC-XWALK-1` `crosswalk_anio_estado_tormentas.csv` — grain año×estado; columns `anio, cve_ent, sids_viento (lista IBTrACS SID, ';'-sep), sids_cono_lluvia, familia_asignada {ciclonica|fluvial|mixta_flag; vacía en filas solo-hazard}, flag_revision, regla_aplicada, version_crosswalk`. Rules `CAL-XWALK-01/02`; **v1.1 delivered** (`CAL-XWALK-03/04`, `data/crosswalk/`, 678 filas, panel 2000–2023 + filas 2024 marcadas fuera de panel). Verification flags feeding the inclusion mask (`DC-CAL-TARGET-4`): `tormenta_sin_perdida`, `fuera_panel_cenapred`, `perdida_sin_tormenta_modelada`, `candidatos_filtrados_huella`, `candidatos_sin_huella`, `nombre_fuzzy`. Companion audit table `eventos_sid_match.csv` (evento_id, nombre_extraido, metodo_match, sids, flag_evento). `FIRM`
- `DC-XWALK-2` `huellas_estatales.csv` — grain evento×estado×peril (solo filas con intensidad > 0); columns `sid, cve_ent, peril {viento|lluvia}, int_max` (m/s | mm acumulados). From `impactcal.hazard.footprints` on the frozen hazards + exposure (provenance chains their sha256). Input of `DC-XWALK-1` v1. `FIRM`

## DC-CAL-EXP — Exposures

- `DC-CAL-EXP-1` `exp_total` (ruta B): LitPop MEX `Exposures`; columns incl. `value (USD→document conversion), cve_ent, region_id, impf_TC, impf_TCSurgeBathtub, impf_TR, impf_RF`. Delivered: `data/exposures/litpop_mex_150as.hdf5` + provenance (`CAL-EXP-04`; 100,369 centroides). `FIRM`
- `DC-CAL-EXP-2` `exp_aseg_{anio}` (ruta A): state sums insured of year, disaggregated ∝ LitPop within state (`CAL-EXP-02`); same columns; value in MXN of year. `PROPOSED`

## DC-CAL-HAZ — Frozen hazards

- `DC-CAL-HAZ-1` Four `Hazard` HDF5 files on **shared centroids** (= exposure coordinates): `haz_tc.h5` (m/s), `haz_surge.h5` (m), `haz_rain.h5` (mm), `haz_rf_{none,flopros}.h5` (m + fraction; **two files** while the protection choice `OQ-CAL-16` is open). Each with `_procedencia.json`: CLIMADA/petals versions, IBTrACS version, timestep, DEM/ISIMIP source, generation date, sha256. `FIRM` (requirement). Delivered 2026-07-14: `haz_tc.h5` + `haz_rain.h5` (`impactcal.hazard.tc`, universe `CAL-HAZ-SHARED-02`, provenance chains exposure + IBTrACS sha256, manifest `haz_tc_rain_20260715T023857Z`). Delivered 2026-07-16: `haz_surge.h5` (`impactcal.hazard.surge`, provenance chains haz_tc + DEM sha256, manifest `haz_surge_20260716T040138Z`) + `haz_rf_{none,flopros}.h5` (`impactcal.hazard.rf`, ISIMIP2a segment 2000–2010, manifest `haz_rf_20260716T040216Z`). Delivered 2026-07-23: **`haz_rf_glofas_{none,flopros}.h5`** (`impactcal.hazard.rf_glofas`, 24 eventos anuales 2000–2023 sobre los mismos 100,369 centroides, 8,594 / 7,752 centroides con agua; provenance encadena los sha256 de las 24 descargas + gumbel-fit + flood-maps + exposición). **Éste es el insumo fluvial de la verosimilitud** (`CAL-RF-04`); `haz_rf_{none,flopros}.h5` (ISIMIP2a 2000–2010) se conserva como validación independiente (`CAL-VAL-01`). Sin huecos en el panel.
- `DC-CAL-HAZ-2` **Frozen raw hazard inputs** (all with `_procedencia.json`): `data/ibtracs/crudos/` (CSVs EP+NA + `IBTrACS.ALL.v04r01.nc`, `CAL-WIND-03`); `data/dem/SRTM15+V2_Mexico.tif` (bbox crop + fillnodata, derived in-repo by `freeze_dem`, `CAL-SURGE-02`); `data/isimip/cama-flood_matsiro_gswp3_*_{none,flopros}_150arcsec_*_1971_2010.nc4` (`CAL-RF-02`); `data/glofas/crudos/glofas-era5_version_4_0_dis24_mexico_{2000..2023}.nc` (24 años, `CAL-RF-03/04`); `data/glofas/auxiliares/{flood-maps.nc, gumbel-fit.nc, FLOPROS_shp_V1/}` (static `rf_glofas` inputs, `CAL-RF-03`; `gumbel-fit.nc` = **edición 1979–2023**, hdl:20.500.11850/726304, malla v4.0 0.05°); `data/marco_geoestadistico/00ent.*` (`CAL-EXP-04`). ISIMIP2b RCP `.nc` pinned in place (fuera del repo). `FIRM`

## DC-CAL-BAYES — Surfaces & posteriors

- `DC-CAL-BAYES-1` Precomputed surfaces: `superficie_{peril}_{ruta}.parquet` — long format `cve_ent, anio, param_valor, perdida_modelada_mxn`; grids per `configs/calibracion.yaml`; provenance sidecar with hazard/exposure hashes. `PROPOSED`
- `DC-CAL-BAYES-2` Posterior traces: `results/trazas/{run_id}.nc` (ArviZ InferenceData). Never the source of truth for parameters — that is `DC-CAL-OUT-1`. `FIRM`

## DC-CAL-OUT — Canonical output

- `DC-CAL-OUT-1` `parametros_impacto_estatal.csv` — grain estado×peril×ruta; columns `cve_ent, estado_nombre, peril, forma_funcional, v_thresh, param_libre, post_media, post_mediana, ci90_inf, ci90_sup, n_anios_efectivos, ruta_target, hash_insumos, version_climada, tag_git, fecha`. Consumed by `construir_impfset.py` (deterministic reconstructor) and by climateCCR. **This is the interface of the whole repo.** `FIRM` (schema)

---

## Related
[[DECISIONS]] · [[GLOSSARY]] · [[00_README_CONTEXT]] · Home: [[_INDEX]]
#arm/cal #type/contracts
