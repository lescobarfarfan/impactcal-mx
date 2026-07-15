# CAL_MOC — Map of Content

The hub for all working notes. Every new `notes/*` note gets linked here (`/new-note` does it).

## Theory
- [[Calibracion_Impacto_Mexico_Master]] — the master design doc (decisions D1–D13, formulas, flujo, referencias, limitaciones, secuencia).

## Pipelines
- [[timestep-convergence-test]] — test de convergencia de timestep (`OQ-CAL-01`): 1 h no converge a grano estatal; recomendación 0.5 h.
- [[hazard-freeze-inputs]] — checklist `OQ-CAL-15`: IBTrACS netCDF + DEM congelados, RCP pineados en sitio; insumo RF histórico resuelto con ISIMIP2a gswp3 1971–2010 (bloque RF calibra 2000–2010).
- [[litpop-exposure]] — exposición LitPop MEX ruta B (`CAL-EXP-01/03`): 150 as, 100k centroides, claves estatales INEGI; la malla definitiva existe.
- [[hazard-tc-generation]] — hazards TC congelados (`DC-CAL-HAZ-1` parcial): `haz_tc.h5` + `haz_rain.h5`, 540 tormentas 2000–2024 sobre la malla definitiva; desbloquea `OQ-CAL-02`.
- [[crosswalk-v1-hazard-side]] — crosswalk v1 (`CAL-XWALK-01/02`): huellas estatales, cono de lluvia 50 mm, desambiguación por huella; cola v0 68→17, 123/220 mixtas resueltas.

## Reading logs
- [[2026-07-12_crosswalk-v0-cenapred]] — crosswalk v0 (loss-side) + frozen CENAPRED/IBTrACS ingestion.
- [[2026-07-12_yagni-ponytail-audit]] — YAGNI discipline (`CAL-GEN-13`) + whole-repo over-engineering audit.
- [[2026-07-14_hazard-freeze-exposures]] — hazard-freeze checklist (`OQ-CAL-15`) + insumo RF dos-segmentos + exposición LitPop (malla definitiva).
- [[2026-07-14_hazard-tc-generation]] — hazards TC congelados: universo near-Mexico (`CAL-HAZ-SHARED-02`), H08 + R-CLIPER v0, referencias de respaldo.
- [[2026-07-14_crosswalk-v1]] — crosswalk v1: escala física del cono 50 mm, analogía EM-DAT para la máscara de inclusión, límite de los best-tracks.

## Canon shortcuts
[[DECISIONS]] · [[DATA_CONTRACTS]] · [[OPEN_QUESTIONS]]

## Related
Home: [[_INDEX]]
#arm/cal #type/moc
