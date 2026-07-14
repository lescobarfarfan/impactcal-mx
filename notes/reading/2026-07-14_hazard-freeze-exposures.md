# Read-log 2026-07-14 — congelamiento de insumos hazard + exposición LitPop

Qué leer y por qué, por decisión del día. Claves en [[REFERENCES]].

**[Tozer2019] — §2–3 (construcción de SRTM15+ V2) y la tabla de fuentes por región.** Respalda `CAL-SURGE-02`: el DEM congelado es un recorte de SRTM15+ V2; hay que poder citar qué mide (topografía+batimetría fusionadas, 15 arcsec) y sus fuentes en la costa mexicana, donde `TCSurgeBathtub` lee la elevación.

**[WillnerISIMIP2024] — página del dataset (DerivedOutputData/Zimmer2023) + el README del pipeline flood-processing.** Respalda `CAL-RF-02`: documenta la cadena descarga→CaMa-Flood→footprints (fit GEV `picontrol`, umbral de descarga 0.1 mm/d, `2005soc`), y las variantes de protección `none`/`flopros` que motivan `OQ-CAL-16`.

**[Sauer2021-ref?] — verificar DOI/título (`OQ-CAL-08`) y leer §Methods.** Es el paper de calibración de daños fluviales sobre estos mismos footprints; el precedente metodológico directo del bloque RF (`CAL-RF-01/02`) y del uso de FLOPROS.

**[Harrigan2020] — §3–4 (evaluación de skill del reanalysis) y §2 (LISFLOOD + ERA5).** Respalda `CAL-RF-03`: los años 2011–2015 entran vía GloFAS-ERA5 v4; el skill por región/cuenca importa para el check de consistencia ISIMIP2a↔GloFAS (`OQ-CAL-17`) — GloFAS-ERA5 y las corridas ISIMIP2a comparten periodo 1979–2010 para el traslape.

**[Eberenz2020LitPop] — §2 (metodología, `fin_mode`, desagregación) y §3.2 (validación por país).** Respalda `CAL-EXP-04`: resolución 150 as, año de referencia y `pc` como modo financiero; la validación para México sostiene el valor total (~3.7×10¹² USD capital producido).

**[PetalsDocs] — tutorial `rf_glofas` (RiverFloodInundation) completo.** Respalda `OQ-CAL-17`: `setup_all()` (mapas JRC, FLOPROS, parámetros Gumbel), `compute()` y las salidas `flood_depth`/`flood_depth_flopros`; es el pipeline exacto de la fase 2.

**[IBTrACSv04r01] — nota técnica de versionado v04r01.** Respalda `CAL-WIND-03`: el freeze-as-is se defiende citando el esquema de re-emisión continua de IBTrACS (el archivo cambia bajo el mismo nombre; `date_created` interno 2025-08-22 es el pin).

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[hazard-freeze-inputs]] · [[litpop-exposure]] · Home: [[_INDEX]]
#arm/cal #type/reading
