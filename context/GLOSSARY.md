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
- **ISIMIP / CaMa-Flood** — inter-sectoral impact model project / global flood model; source of RF NetCDFs.
- **GloFAS** — Global Flood Awareness System (CDS); fase-2 fluvial refinement.
- **`_procedencia.json`** — per-artifact provenance sidecar (`CAL-GEN-02`).

## J. Content-word retrieval index

| Topic | Search phrase |
|---|---|
| The two-route design | **ruta asegurada CNSF sumas aseguradas ruta total CENAPRED LitPop sensibilidad** |
| Hazard consistency decision | **CLIMADA autocontenido v_half absorbs wind-model bias no transferable** |
| The calibration unit | **año estado anual agregado multi-storm ambiguity EM-DAT overlap** |
| The deflator decision | **INPC INEGI pesos constantes deflactor GDP rejected FIX Banxico** |
| Timestep decision + anomaly | **timestep convergencia 1h Eberenz finer timestep lower losses frozen** |
| The functional form | **from_emanuel_usa v_thresh 25.7 fixed scale 1 single free v_half identifiability** |
| Depth-damage scaling | **JRC NorthAmerica residential kappa MDD multiplicative scalar clipped** |
| The hierarchical model | **partial pooling log v_half regional groups hyperprior Eberenz NA anchor lognormal likelihood** |
| The surrogate trick | **precomputed surface L_st monotone PCHIP interpolation PyMC never calls CLIMADA** |
| Multi-peril combination | **union of damage 1 minus product fractions HAZUS shared centroids double counting** |
| Identifiability of the split | **asymmetric priors wind free water anchored event signatures posterior correlation** |
| The crosswalk rules | **crosswalk año estado SID cono lluvia familia asignada flag revision** |
| Inland cyclone losses | **CDMX remanentes ciclónicos inundación peril CNSF interior states** |
| Pluvial gap | **pluvial urbano drenaje CDMX fuera de alcance CHIRPS piloto** |
| The canonical output | **parametros_impacto_estatal.csv construir_impfset reconstructor never pickles** |
| Merge with climateCCR | **CAL prefix HAZ-CLIMADA import crosswalk parameter table interface OQ-CAL-12** |

---

## Related
[[DECISIONS]] · [[DATA_CONTRACTS]] · [[REFERENCES]] · Home: [[_INDEX]]
#arm/cal #type/glossary
