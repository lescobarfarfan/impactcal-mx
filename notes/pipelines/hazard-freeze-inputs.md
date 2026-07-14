# Congelamiento de insumos hazard (OQ-CAL-15)

**Pipelines:** `impactcal.hazard.ibtracs` (extendido) + `impactcal.hazard.freeze_inputs` (nuevo) · ejecutados 2026-07-14 · checklist [[OPEN_QUESTIONS]] `OQ-CAL-15`, ítems `OQ-CAL-05`/`OQ-CAL-06`.

## Qué quedó pineado

**IBTrACS netCDF (caché CLIMADA).** `~/climada/data/IBTrACS.ALL.v04r01.nc` congelado **tal cual** en `data/ibtracs/crudos/` con `_procedencia.json` (sha256, `date_created` interno 2025-08-22, doi:10.25921/82ty-9e16). Decisión *freeze-as-is*, no refresh: su cobertura (hasta 2025-08) cubre todo el periodo `CAL-TARGET-02`, y es el archivo que leyeron el test de timestep y el crosswalk v0 — refrescarlo desincronizaría los CSVs crudos ya congelados de la misma versión. La generación de viento futura debe verificar que la caché siga hash-idéntica a la copia congelada (o restaurarla desde ella) antes de correr. [Knapp2010][IBTrACSv04r01]

**DEM (marejada, `CAL-SURGE-01`).** `SRTM15+V2_Mexico.tif` (15 arcsec, LZW) congelado en `data/dem/`; identificado como **SRTM15+ V2** [Tozer2019]: recorte del raster global (3.4 GB, sha256 registrado como `origen_global_sha256`) al polígono nacional INEGI `00ent` vía `rasterio.mask`, sin remuestreo (notebook `Procesa_Raster_Altitud.ipynb` junto al origen). *Caveat para la generación de marejada:* el recorte es exacto al polígono (sin buffer costero) — verificar que los centroides costeros no caigan en nodata; si sí, re-recortar con buffer desde el global pineado. `hazard.dem_path` en config apunta a la copia congelada.

**ISIMIP fluvial (`CAL-RF-01`).** Los 6 `.nc` en mano (`{26,60,85}_{flddph,fldfrc}_150arcsec_matsiro_hadgem2-es_0.nc`) pineados **en sitio** (sidecar junto a cada archivo, no copiados a `data/`): son **ISIMIP2b, escenarios RCP 2.6/6.0/8.5, 2006–2100, clima GCM (HadGEM2-ES) + GHM MATSIRO, CaMa-Flood 3.6.2**, generados con flood-processing de S. Willner (doi:10.5281/zenodo.1241051, `[Sauer2021-ref?]`).

## Hallazgo y resolución (para `/digest`)

Los `.nc` ISIMIP2b en mano **no sirven para la calibración histórica**: son proyecciones RCP 2006–2100 con clima simulado por GCM — no cubren 2000–2005 y sus años no corresponden a años meteorológicos observados, así que no pueden emparejarse con pérdidas observadas año×estado (`CAL-TARGET-02`). Quedan pineados para la aplicación prospectiva aguas abajo.

**Resolución (2026-07-14):** descargados los footprints **ISIMIP2a con forzamiento observado** — `cama-flood_matsiro_gswp3_nobc_hist_nosoc_co2_{flddph,fldfrc}_{none,flopros}_150arcsec_global_annual_1971_2010.nc4` (ISIMIP Repository, DerivedOutputData/Zimmer2023, doi:10.48364/ISIMIP.303619; sha512 oficiales verificados, `SHA512SUMS.isimip` junto a los crudos) a `climateCCR/data/hazard_mx/datos_ISIMIP/crudos/`, congelados en `data/isimip/` vía `freeze_inputs`. GHM MATSIRO consistente con los RCP en mano; se bajaron ambas variantes de protección (`none` y `flopros`) — cuál entra en la likelihood es decisión pendiente. **Limitación residual:** ISIMIP2a termina en **2010** → el bloque RF solo calibra 2000–2010 del panel 2000–2015; cobertura completa requeriría la vía GloFAS/ERA5 (fase 2, `CAL-RF-01`). Propuestas para `/digest`: (i) decisión protección none vs flopros; (ii) decisión ventana RF 2000–2010 documentada o fase-2 GloFAS.

## Años faltantes 2011–2015: vía GloFAS/ERA5 (fase 2 activada)

Para los años del panel sin ISIMIP2a, el insumo es la **descarga fluvial diaria GloFAS-ERA5** (reanalysis 1979–presente, 0.05°, doi:10.24381/cds.a4fdd6b9), hoy servida por el **CEMS Early Warning Data Store** (EWDS — los datasets `cems-glofas-*` migraron ahí desde el CDS; el token ECMWF de `~/.cdsapirc` sirve para ambos). Descarga vía `impactcal.hazard.glofas` (config `glofas:`, 1 NetCDF/año 2011–2015, bbox México, procedencia con el request completo). Verificado end-to-end salvo la licencia **"CEMS-FLOODS datasets licence"** (aceptación manual en el portal EWDS). Los footprints se computarán después con `climada_petals.hazard.rf_glofas.RiverFloodInundation` (disponible en `climada_env`, petals 6.1.0), que produce `flood_depth` y `flood_depth_flopros` — las mismas dos variantes de protección que los ISIMIP2a congelados, así que la decisión none/flopros aplica pareja a ambos tramos. Consistencia ISIMIP2a↔GloFAS en años de traslape: pendiente de diseño (candidato a `OQ-CAL`).

## Re-confirmación 0.5 h en la malla definitiva (2026-07-14)

Con la malla definitiva ya existente ([[litpop-exposure]], LitPop 150 as), corrida `timestep_test_20260714T184936Z` (0.25 vs 0.5 h, 4 tormentas, config del run en su manifest): **0.5 h se sostiene** — pérdida agregada relativa 0.998 (Wilma), 0.989 (Odile), 0.940 (Patricia), 0.937 (Willa), idéntica a la corrida del 2026-07-13; swath RMSE ≤ 1.92 m/s, |sesgo| ≤ 0.35 m/s. Grano estatal ≥ 0.92 en general (Nayarit-Patricia 1.009 — el hueco del caso 1 h no aparece); **un outlier a documentar: Patricia/Colima captura 0.64 del referente** (estado pequeño en el punto exacto de landfall de la tormenta más rápida; sesgo consistente absorbible por `v_half`, `CAL-WIND-02`). NaN = estados con pérdida ~0 en el referente (artefacto documentado tipo SLP).

## Estado del checklist `OQ-CAL-15`

Pin IBTrACS ✓ · procedencia DEM (`OQ-CAL-05`) ✓ · procedencia ISIMIP (`OQ-CAL-06`) ✓ con hallazgo resuelto (ISIMIP2a + GloFAS) · re-confirmación 0.5 h vs 0.25 h en malla definitiva ✓ (outlier Colima documentado) — **checklist completo**, cierre formal en `/digest`.

## Uso

```bash
python -m impactcal.hazard.ibtracs --modo ingerir|verificar        # CSVs + netCDF caché
python -m impactcal.hazard.freeze_inputs --modo ingerir|verificar  # DEM + pins ISIMIP
```

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[timestep-convergence-test]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
