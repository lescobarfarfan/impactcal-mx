# GLOSSARY — impactcal-mx

Terms, acronyms, proper nouns — one line each. Spanish identifiers verbatim (`CAL-GEN-08`).
§J is the **content-word retrieval index** (search phrases that reliably recall each topic).

## A. Perils & hazard

- **TropCyclone / `TC`** — CLIMADA wind hazard from IBTrACS tracks (m/s, sustained wind at centroids).
- **TCSurgeBathtub** — petals surge hazard (m): simplified Xu (2010) wind-surge relation + inland decay over a DEM; bathtub model.
- **TCRain / `TR`** — petals cyclonic-rain hazard (mm accumulated per storm); models R-CLIPER / TCR.
- **RiverFlood / `RF`** — petals fluvial hazard from ISIMIP/CaMa-Flood NetCDF: depth (m) + flooded fraction; annual maximum.
- **Marejada** — storm surge (kept in Spanish where it names data/labels).
- **Cono de lluvia** — the inland rain footprint of a cyclone; defines inland affected states (`CAL-XWALK-01`).
- **IBTrACS SID** — unique storm identifier; key of the crosswalk.

## B. Impact functions

- **Emanuel sigmoid** — `f(V) = v_n³/(1+v_n³)`, `v_n = max(V−V_thresh,0)/(V_half−V_thresh)`; wind→damage fraction.
- **`v_thresh`** — no-damage wind threshold, fixed at 25.7 m/s (`CAL-IMPF-01`).
- **`v_half`** — wind at 50% damage; THE free parameter per state.
- **`κ_s` (kappa)** — state multiplicative scalar on the JRC depth-damage MDD (`CAL-IMPF-02`).
- **JRC curve** — Huizinga et al. (2017) global depth-damage functions; NorthAmerica/residential base.
- **MDD / PAA** — mean damage degree / percentage of affected assets (CLIMADA `ImpactFunc` components).
- **`impf_TC` / `impf_RF` / …** — Exposures columns assigning an impact-function ID per point; here = clave INEGI.

## C. Calibration

- **Partial pooling** — hierarchical shrinkage of state parameters toward a regional mean (Gelman-Hill).
- **Precomputed surface / superficie** — tabulated `L_st(param)` from CLIMADA; the PyMC likelihood interpolates it (PCHIP), never calls CLIMADA (`CAL-BAYES-02`).
- **Null model / modelo nulo** — Eberenz scheme: wind-only vs total losses; `v_half` absorbs surge+rain.
- **Union-of-damage rule** — `f_total = 1 − Π(1−f_i)` at cell level (`CAL-MULTI-01`).
- **RMSF / MSLE** — log-space cost functions; losses span orders of magnitude.
- **`BayesianOptimizer`** — climada.util.calibrate GP-search optimizer; Bayesian *optimization*, not inference.
- **Ruta A / Ruta B** — insured (CNSF) vs total (CENAPRED) calibration targets (`CAL-TARGET-01`).

## D. Data & institutions

- **CNSF** — Comisión Nacional de Seguros y Fianzas; microdata source; loss variable `MONTO PAGADO`.
- **CENAPRED** — Centro Nacional de Prevención de Desastres; *Impacto Socioeconómico de los Desastres en México* annual series (total losses).
- **Sumas aseguradas** — sums insured; ruta A exposure (`CAL-EXP-02`).
- **LitPop** — nightlights × GDP asset-exposure proxy (Eberenz et al. 2020).
- **INPC** — Índice Nacional de Precios al Consumidor (INEGI); the deflator (`CAL-TARGET-03`).
- **Marco Geoestadístico** — INEGI state polygons; `cve_ent` 2-digit key (`DC-CONV-5`).
- **ISIMIP / CaMa-Flood** — inter-sectoral impact model project / global flood model; source of RF NetCDFs. **ISIMIP2a** = observed-forcing runs (calibration input, 1971–2010); **ISIMIP2b** = GCM-forced scenario runs (prospective use only, `CAL-RF-02`).
- **GloFAS** — Global Flood Awareness System; GloFAS-ERA5 daily discharge reanalysis (1979–present) covers panel years 2011–2015 (`CAL-RF-03`).
- **EWDS** — CEMS Early Warning Data Store (ewds.climate.copernicus.eu); serves the `cems-glofas-*` datasets (migrated from the CDS; same ECMWF token, own licences incl. CEMS-FLOODS).
- **FLOPROS** — global database of flood protection standards; the `flopros` protection variant of ISIMIP2a/`rf_glofas` footprints (`OQ-CAL-16`).
- **`rf_glofas`** — petals module turning GloFAS discharge into flood footprints (annual max → Gumbel return period → JRC hazard-map interpolation → FLOPROS protection); serves RF 2011–2015 (`OQ-CAL-17`). Static inputs frozen in `data/glofas/auxiliares/`.
- **`_procedencia.json`** — per-artifact provenance sidecar (`CAL-GEN-02`).
- **Consolidados CENAPRED** — the four frozen outputs of the climateCCR pipeline (panel año×estado×peril, eventos, multiestado, catálogo); the CENAPRED interface of this repo (`CAL-TARGET-04`), 2000–2015.
- **`freeze_copy`** — `impactcal.infra.freeze`: idempotent copy of external inputs into `data/<fuente>/` with sha256 verification + provenance sidecar (`CAL-GEN-02/12`).

## J. Content-word retrieval index

| Topic | Search phrase |
|---|---|
| The two-route design | **ruta asegurada CNSF sumas aseguradas ruta total CENAPRED LitPop sensibilidad** |
| Hazard consistency decision | **CLIMADA autocontenido v_half absorbs wind-model bias no transferable** |
| The calibration unit | **año estado anual agregado multi-storm ambiguity EM-DAT overlap** |
| The deflator decision | **INPC INEGI pesos constantes deflactor GDP rejected FIX Banxico** |
| Timestep decision + anomaly | **timestep 0.5h congelado convergencia submuestreo swath Patricia Nayarit finer timestep lower losses explicado** |
| The functional form | **from_emanuel_usa v_thresh 25.7 fixed scale 1 single free v_half identifiability** |
| Depth-damage scaling | **JRC NorthAmerica residential kappa MDD multiplicative scalar clipped** |
| The hierarchical model | **partial pooling log v_half regional groups hyperprior Eberenz NA anchor lognormal likelihood** |
| The surrogate trick | **precomputed surface L_st monotone PCHIP interpolation PyMC never calls CLIMADA** |
| Multi-peril combination | **union of damage 1 minus product fractions HAZUS shared centroids double counting** |
| Identifiability of the split | **asymmetric priors wind free water anchored event signatures posterior correlation** |
| The crosswalk rules | **crosswalk año estado SID cono lluvia familia asignada flag revision** |
| Crosswalk v0 matching | **v0 nombres fechas empate CENAPRED IBTrACS ventana buffer mixta_flag typo Julette candidatos multiples** |
| The frozen ingestion | **ingesta congelada freeze_copy consolidados climateCCR sha256 procedencia fuentes_externas** |
| Inland cyclone losses | **CDMX remanentes ciclónicos inundación peril CNSF interior states** |
| Pluvial gap | **pluvial urbano drenaje CDMX fuera de alcance CHIRPS piloto** |
| The canonical output | **parametros_impacto_estatal.csv construir_impfset reconstructor never pickles** |
| Merge with climateCCR | **CAL prefix HAZ-CLIMADA import crosswalk parameter table interface OQ-CAL-12** |
| The YAGNI discipline | **YAGNI minimal one-line simplest stdlib no speculative abstraction ponytail audit** |
| Frozen hazard inputs | **checklist congelamiento IBTrACS date_created freeze-as-is DEM SRTM15 recorte 00ent sha512 oficial** |
| The RF two-segment input | **ISIMIP2a gswp3 matsiro 2000-2010 GloFAS-ERA5 2011-2015 EWDS cems-glofas-historical licencia CEMS-FLOODS none flopros** |
| The definitive grid | **malla definitiva LitPop 150 arcsec 100369 centroides claves estatales nearest fallback EPSG 6372** |
| Timestep re-confirmation | **re-confirmación malla definitiva 0.5 h se sostiene outlier Colima 0.64 landfall Patricia** |
| The frozen TC hazards | **haz_tc haz_rain generación 540 tormentas universo near-Mexico bbox estimate_missing temporada_max 2024 H08 R-CLIPER caché hash restaurada** |
| Crosswalk v1 hazard-side | **crosswalk v1 huellas estatales cono lluvia 50 mm umbral desambiguación candidatos por huella fuzzy Julette tormenta_sin_perdida solo hazard 123 mixtas resueltas** |
| The DEM nodata fix | **DEM bbox crop fillnodata lagunas Ojo de Liebre Términos Clarión petals descarta en silencio chequeo costero 251 a 0 huecos raster pineado** |
| The frozen surge hazard | **haz_surge bañera Xu decaimiento 0.2 m/km SLR 0 herencia haz_tc 79 eventos máximo 5.79** |
| The frozen RF footprints | **haz_rf none flopros ISIMIP2a 2000-2010 celda a celda saneador NaN CaMa frequency sin significado dos artefactos** |
| The GloFAS aux freeze | **auxiliares rf_glofas flood-maps gumbel-fit MD5 DSpace URL petals rota HTML FLOPROS ediciones 641667 726304 v4.0** |

---

## Related
[[DECISIONS]] · [[DATA_CONTRACTS]] · [[REFERENCES]] · Home: [[_INDEX]]
#arm/cal #type/glossary
