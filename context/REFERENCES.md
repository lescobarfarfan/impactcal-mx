# REFERENCES — Verified bibliography

Each entry was checked against a primary/authoritative source (or carried over verified from the
origin project canon) and lists the decision ID(s) it backs. Citation keys are used throughout the
canon. **§99 To confirm:** cited in the project but edition/DOI/journal not independently
re-verified — do not cite in the manuscript until checked (tracked in `OPEN_QUESTIONS.md`).

---

## 1. Impact functions & calibration

- **`[Emanuel2011]`** — Emanuel, K. (2011). *Global Warming Effects on U.S. Hurricane Damage.* Weather, Climate, and Society, 3(4), 261–268. DOI: 10.1175/WCAS-D-11-00007.1 — Backs `CAL-IMPF-01`.
- **`[Eberenz2021]`** — Eberenz, S., Lüthi, S., & Bresch, D. N. (2021). *Regional tropical cyclone impact functions for globally consistent risk assessments.* NHESS, 21(1), 393–415. DOI: 10.5194/nhess-21-393-2021. Code: Zenodo DOI 10.5281/zenodo.4467858 — Backs `CAL-SCOPE-01/03`, `CAL-TARGET-01/02`, `CAL-WIND-02`, `CAL-IMPF-01`, `CAL-BAYES-01/03`, `CAL-MULTI-02`, `CAL-VAL-01` (`v_thresh = 25.7 m/s`; NA regional `v_half = 74.7 m/s` as prior anchor).
- **`[Eberenz2020LitPop]`** — Eberenz, S., Stocker, D., Röösli, T., & Bresch, D. N. (2020). *Asset exposure data for global physical risk assessment (LitPop).* ESSD, 12(2), 817–833. DOI: 10.5194/essd-12-817-2020 — Backs `CAL-EXP-01/02`.
- **`[Huizinga2017]`** — Huizinga, J., De Moel, H., & Szewczyk, W. (2017). *Global flood depth-damage functions: Methodology and the database with guidelines.* EUR 28552 EN, Publications Office of the European Union. DOI: 10.2760/16510 — Backs `CAL-IMPF-02`, `CAL-MULTI-02`.
- **`[AznarSiguan2019]`** — Aznar-Siguan, G., & Bresch, D. N. (2019). *CLIMADA v1: a global weather and climate risk assessment platform.* Geoscientific Model Development, 12, 3085–3097. DOI: 10.5194/gmd-12-3085-2019 — Platform citation.

## 2. Tropical-cyclone hazard

- **`[Knapp2010]`** — Knapp, K. R., Kruk, M. C., Levinson, D. H., Diamond, H. J., & Neumann, C. J. (2010). *The International Best Track Archive for Climate Stewardship (IBTrACS).* BAMS, 91(3), 363–376. DOI: 10.1175/2009BAMS2755.1 — Backs `CAL-WIND-01`.
- **`[IBTrACSv04r01]`** — Gahtan, J., Knapp, K. R., Schreck, C. J., Diamond, H. J., Kossin, J. P., & Kruk, M. C. (2024). *IBTrACS Project, Version 4r01.* NOAA NCEI. DOI: 10.25921/82ty-9e16 — Backs `CAL-WIND-01` (cite paper + dataset DOI).
- **`[Tozer2019]`** — Tozer, B., Sandwell, D. T., Smith, W. H. F., Olson, C., Beale, J. R., & Wessel, P. (2019). *Global bathymetry and topography at 15 arc sec: SRTM15+.* Earth and Space Science, 6, 1847–1864. DOI: 10.1029/2019EA000658 — Backs `CAL-SURGE-01/02`. Note: the pinned global copy carries sparse nodata voids (not present in the pristine product; filled at freeze, `CAL-SURGE-02`).
- **`[Tuleya2007]`** — Tuleya, R. E., DeMaria, M., & Kuligowski, R. J. (2007). *Evaluation of GFDL and simple statistical model rainfall forecasts for U.S. landfalling tropical storms.* Weather and Forecasting, 22(1), 56–70. DOI: 10.1175/WAF972.1 — Backs `CAL-RAIN-01` (R-CLIPER).
- **`[Lu2018]`** — Lu, P., Lin, N., Emanuel, K., Chavas, D., & Smith, J. (2018). *Assessing hurricane rainfall mechanisms using a physics-based model.* Journal of the Atmospheric Sciences, 75(7), 2337–2358. DOI: 10.1175/JAS-D-17-0264.1 — Backs `CAL-RAIN-01` (TCR).

## 2b. Fluvial hazard

- **`[WillnerISIMIP2024]`** — Willner, S., Sauer, I., Novak, L., & Otto, C. (2024). *Global simulations of fluvial floods based on the ISIMIP2 ensemble of global hydrological models (v1.0).* ISIMIP Repository (DerivedOutputData/Zimmer2023). DOI: 10.48364/ISIMIP.303619 — Backs `CAL-RF-02` (dataset DOI + portal verified 2026-07-14; sha512 of the frozen files verified against the repository).
- **`[Harrigan2020]`** — Harrigan, S., Zsoter, E., Alfieri, L., Prudhomme, C., Salamon, P., Wetterhall, F., Barnard, C., Cloke, H., & Pappenberger, F. (2020). *GloFAS-ERA5 operational global river discharge reanalysis 1979–present.* Earth System Science Data, 12(3), 2043–2060. DOI: 10.5194/essd-12-2043-2020 — Backs `CAL-RF-03` (verified 2026-07-14 against the ESSD page; dataset DOI 10.24381/cds.a4fdd6b9).

## 3. Statistics

- **`[GelmanHill2007]`** — Gelman, A., & Hill, J. (2007). *Data Analysis Using Regression and Multilevel/Hierarchical Models.* Cambridge University Press. — Backs `CAL-BAYES-01/03` (partial pooling).

## 4. Software documentation (pin versions in `environment.lock.yml`)

- **`[CLIMADAdocs]`** — CLIMADA v6 documentation: `climada.util.calibrate`, `TropCyclone`, `LitPop`. climada-python.readthedocs.io — Backs `CAL-BAYES-01` usage.
- **`[PetalsDocs]`** — climada-petals v6 documentation: `TCSurgeBathtub`, `TCRain`, `RiverFlood`, `ImpfRiverFlood`, GloFAS module. climada-petals.readthedocs.io — Backs `CAL-SURGE-01`, `CAL-RAIN-01`, `CAL-RF-01`.

---

## §99 — To confirm (GEN rule: never cite these until verified)

- **`[Xu2010]`** — Xu, L. (2010). Wind-surge relationship from pre-run SLOSH outputs, as cited by the `TCSurgeBathtub` documentation. Exact document type/venue unverified — cite via `[PetalsDocs]` until located. → `OQ-CAL-08`
- **`[Sauer2021-ref?]`** — Sauer, I. J., et al. (2021). River-flood damage calibration under regional disaggregation (CLIMADA/PIK). Journal recorded as *Nature Communications* 12:2128, DOI 10.1038/s41467-021-22153-9 in the design doc — **confirm DOI + exact title before manuscript use.** → `OQ-CAL-08`
- **`[Hazus-ref?]`** — FEMA, *Hazus Hurricane Model Technical Manual* (combined wind-flood loss methodology). **Exact current edition/URL to pin.** Backs `CAL-MULTI-01`. → `OQ-CAL-08`
- **`[Wagenaar2018-ref?]`** — Wagenaar, D., Lüdtke, S., Schröter, K., Bouwer, L. M., & Kreibich, H. (2018). Flood-damage-model transferability. **Journal uncertain (Water Resources Research vs Risk Analysis) — verify.** Context for `CAL-IMPF-02`. → `OQ-CAL-08`
- **`[Dottori2016-ref?]`** — JRC global river flood hazard maps rp10–rp500 (cidportal.jrc.ec.europa.eu, FLOODS/GlobalMaps), presumably Dottori, F., et al. (2016). *Development and evaluation of a framework for global flood hazard mapping.* Advances in Water Resources. **Confirm exact citation + dataset version before manuscript.** Backs `CAL-RF-03` (frozen `flood-maps.nc`). → `OQ-CAL-08`
- **`[Scussolini2016-ref?]`** — Scussolini, P., et al. (2016). *FLOPROS: an evolving global database of flood protection standards.* NHESS 16, 1049–1067. DOI: 10.5194/nhess-16-1049-2016. The frozen `FLOPROS_shp_V1` is the article's supplement zip (URL matches journal/volume/pages). **Confirm author list/pages before manuscript.** Backs `CAL-RF-03`, `OQ-CAL-16`. → `OQ-CAL-08`
- **`[GumbelGloFAS-ref?]`** — *Gumbel distribution fit parameters for historical GloFAS river discharge data (1979–2015).* ETH Research Collection dataset, hdl:20.500.11850/641667 (companion data of petals `rf_glofas`; a 1979–2023 edition exists, hdl:20.500.11850/726304). **Dataset authors/DOI to confirm.** Backs `CAL-RF-03` (frozen `gumbel-fit.nc`, repository MD5 verified). → `OQ-CAL-08`

---

## Related
[[DECISIONS]] · [[OPEN_QUESTIONS]] · Home: [[_INDEX]]
#arm/cal #type/references
