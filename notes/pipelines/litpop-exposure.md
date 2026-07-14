# Exposición LitPop MEX (ruta B)

**Pipeline:** `impactcal.exposure.litpop` · ejecutado 2026-07-14 · decisiones [[DECISIONS]] `CAL-EXP-01`/`CAL-EXP-03`, contrato `DC-CAL-EXP-1` · artefacto `data/exposures/litpop_mex_150as.hdf5` + `_procedencia.json` + manifest.

**Construcción.** `LitPop.from_countries(['MEX'])` a **150 arcsec** (~4.6 km; decisión de resolución a ratificar en `/digest`: el test de timestep mostró 150≈300 en viento y la marejada pide grano fino; config `exposure.resolucion_arcsec`), año de referencia 2018, `fin_mode='pc'` (defaults LitPop [Eberenz2020LitPop]; GPW v4.11 usa 2020, el año más cercano disponible — registrado en procedencia). Resultado: **100,369 centroides**, valor total **≈ 3.70 × 10¹² USD** (capital producido; orden de magnitud consistente con las cuentas de riqueza del Banco Mundial para México). Valores en USD del año de referencia; conversión a MXN documentada aguas abajo (`DC-CAL-EXP-1`).

**Claves estatales (`CAL-EXP-03`).** `cve_ent`/`region_id` = clave INEGI por *spatial join* con el Marco Geoestadístico `00ent` (32 entidades, congelado en `data/marco_geoestadistico/` con procedencia; **versión del Marco por confirmar** — el shapefile local no la registra). Join `within` en EPSG:4326 con *fallback* al estado más cercano en EPSG:6372 (proyectado, nativo de la capa) para celdas costeras fuera del polígono; puntos en frontera toman el primer match. Verificado: 32 estados presentes, sin claves faltantes, `impf_TC = impf_TCSurgeBathtub = impf_TR = impf_RF = region_id` en todas las celdas.

**Malla definitiva.** Estos centroides son la malla compartida de los cuatro hazards (`CAL-HAZ-SHARED-01`); su existencia desbloquea la re-confirmación 0.5 h vs 0.25 h (`OQ-CAL-15`) y el crosswalk v1 (`OQ-CAL-02`). Ruta A (sumas aseguradas CNSF, `CAL-EXP-02`, `DC-CAL-EXP-2`) sigue bloqueada en `OQ-CAL-11`.

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[DATA_CONTRACTS]] · [[OPEN_QUESTIONS]] · [[hazard-freeze-inputs]] · [[timestep-convergence-test]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
