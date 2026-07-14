# Congelamiento de insumos hazard (OQ-CAL-15)

**Pipelines:** `impactcal.hazard.ibtracs` (extendido) + `impactcal.hazard.freeze_inputs` (nuevo) · ejecutados 2026-07-14 · checklist [[OPEN_QUESTIONS]] `OQ-CAL-15`, ítems `OQ-CAL-05`/`OQ-CAL-06`.

## Qué quedó pineado

**IBTrACS netCDF (caché CLIMADA).** `~/climada/data/IBTrACS.ALL.v04r01.nc` congelado **tal cual** en `data/ibtracs/crudos/` con `_procedencia.json` (sha256, `date_created` interno 2025-08-22, doi:10.25921/82ty-9e16). Decisión *freeze-as-is*, no refresh: su cobertura (hasta 2025-08) cubre todo el periodo `CAL-TARGET-02`, y es el archivo que leyeron el test de timestep y el crosswalk v0 — refrescarlo desincronizaría los CSVs crudos ya congelados de la misma versión. La generación de viento futura debe verificar que la caché siga hash-idéntica a la copia congelada (o restaurarla desde ella) antes de correr. [Knapp2010][IBTrACSv04r01]

**DEM (marejada, `CAL-SURGE-01`).** `SRTM15+V2_Mexico.tif` (15 arcsec, LZW) congelado en `data/dem/`; identificado como **SRTM15+ V2** [Tozer2019]: recorte del raster global (3.4 GB, sha256 registrado como `origen_global_sha256`) al polígono nacional INEGI `00ent` vía `rasterio.mask`, sin remuestreo (notebook `Procesa_Raster_Altitud.ipynb` junto al origen). *Caveat para la generación de marejada:* el recorte es exacto al polígono (sin buffer costero) — verificar que los centroides costeros no caigan en nodata; si sí, re-recortar con buffer desde el global pineado. `hazard.dem_path` en config apunta a la copia congelada.

**ISIMIP fluvial (`CAL-RF-01`).** Los 6 `.nc` en mano (`{26,60,85}_{flddph,fldfrc}_150arcsec_matsiro_hadgem2-es_0.nc`) pineados **en sitio** (sidecar junto a cada archivo, no copiados a `data/`): son **ISIMIP2b, escenarios RCP 2.6/6.0/8.5, 2006–2100, clima GCM (HadGEM2-ES) + GHM MATSIRO, CaMa-Flood 3.6.2**, generados con flood-processing de S. Willner (doi:10.5281/zenodo.1241051, `[Sauer2021-ref?]`).

## Hallazgo (para `/digest`)

Los `.nc` ISIMIP en mano **no sirven para la calibración histórica**: son proyecciones RCP 2006–2100 con clima simulado por GCM — no cubren 2000–2005 y sus años no corresponden a años meteorológicos observados, así que no pueden emparejarse con pérdidas observadas año×estado (`CAL-TARGET-02`). El insumo RF de calibración requiere corridas con forzamiento observado (ISIMIP2a — p. ej. GSWP3/WATCH — del mismo dataset de Willner, o la vía GloFAS ya reservada como fase 2 en `CAL-RF-01`). Propuesta: nueva `OQ-CAL` "obtener footprints fluviales históricos"; los RCP pineados quedan para la aplicación prospectiva aguas abajo.

## Estado del checklist `OQ-CAL-15`

Pin IBTrACS ✓ · procedencia DEM (`OQ-CAL-05`) ✓ · procedencia ISIMIP (`OQ-CAL-06`) ✓ con hallazgo · re-confirmación 0.5 h vs 0.25 h **pendiente**: espera la malla definitiva de exposición (paso 3, `CAL-EXP-*`; la resolución LitPop aún no está fijada), igual que la v1 del crosswalk (`OQ-CAL-02`).

## Uso

```bash
python -m impactcal.hazard.ibtracs --modo ingerir|verificar        # CSVs + netCDF caché
python -m impactcal.hazard.freeze_inputs --modo ingerir|verificar  # DEM + pins ISIMIP
```

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[timestep-convergence-test]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
