# Calibración de funciones de impacto subnacionales para México en CLIMADA

**Rama:** calibración de funciones de daño ad-hoc (estatal) — fenómenos hidrometeorológicos
**Estado:** diseño aprobado, pre-implementación
**Última actualización:** 2026-07-08 (incorporado al repo; las decisiones D1–D13 están indexadas en [[DECISIONS]] como `CAL-*`)

> Este es el documento maestro en prosa. La versión canónica de una línea de cada decisión vive en [[DECISIONS]]; si hay conflicto, gana el canon.

---

## 1. Objetivo y motivación

Las funciones de impacto incluidas en CLIMADA agrupan a México dentro de la región "Latinoamérica y el Caribe", perdiendo heterogeneidad subnacional relevante para la evaluación de riesgos focalizados. Eberenz, Lüthi y Bresch (2021) demuestran que usar una sola función de impacto calibrada para EE.UU. a nivel global sesga el daño simulado hasta por un factor de 36 en algunas regiones, y proponen calibración regional de la función de Emanuel (2011) contra daños reportados (EM-DAT, nivel país-evento).

**Este proyecto lleva esa lógica un nivel más abajo:** funciones de impacto por entidad federativa, calibradas contra microdatos de pérdidas CNSF (aseguradas) y CENAPRED (totales), aprovechando que CLIMADA permite asignar una función de impacto distinta a cada punto de exposición vía la columna `impf_*` del `GeoDataFrame` de `Exposures`.

**Alcance de perils (fase 1):** viento ciclónico (`TropCyclone`), marejada ciclónica (`TCSurgeBathtub`, climada-petals), lluvia ciclónica (`TCRain`, climada-petals), inundación fluvial independiente (`RiverFlood`, climada-petals). Fuera de alcance (documentado en §9): inundación pluvial/urbana.

---

## 2. Decisiones de diseño (indexadas en [[DECISIONS]])

| # | Canon ID | Decisión | Justificación / referencia |
|---|----------|----------|---------------------------|
| D1 | `CAL-TARGET-01` | Dos rutas de calibración: (A) pérdidas aseguradas CNSF vs exposición asegurada; (B) pérdidas totales CENAPRED vs LitPop. B = sensibilidad de A. | Baja penetración del seguro; dos targets *independientes*; consistencia interna pérdidas↔exposición por ruta. `[Eberenz2021]` |
| D2 | `CAL-SCOPE-03` | Hazard autocontenido en CLIMADA (no el pipeline propio IBTrACS/Holland). | Una función calibrada con un modelo de viento no es transferible a otro: `v_half` absorbe los sesgos del hazard. La aplicación downstream ocurre en CLIMADA. |
| D3 | `CAL-TARGET-02` | Unidad de calibración: **año × estado**. | CNSF es anual; multi-tormenta por año-estado hace ambigua la atribución por evento; análogo al manejo de solapamientos de Eberenz con EM-DAT. |
| D4 | `CAL-TARGET-02` | Periodo: **2000–presente**. | Acotado por el lado de pérdidas (CENAPRED ~2000), no por IBTrACS (~1980, era satelital EP). No se inventan pérdidas hacia atrás. |
| D5 | `CAL-TARGET-03` | Deflactación con **INPC (INEGI)**, año base = último año completo. | Serie doméstica MXN → deflactor doméstico oficial. Deflactores PIB (BM/FMI) rechazados. USD (FIX Banxico) solo para comparar magnitudes con literatura. |
| D6 | `CAL-IMPF-01` | Sigmoide de Emanuel (2011) vía `ImpfTropCyclone.from_emanuel_usa`; `v_thresh = 25.7` m/s y `scale = 1` **fijos**; único parámetro libre `v_half` por estado. | El constructor implementa la forma general ("usa" solo nombra sus defaults). Identificabilidad: liberar dos parámetros de forma con pérdidas agregadas produce valles planos. Sensibilidad opcional `v_thresh ∈ {20, 25.7, 30}`. `[Emanuel2011]` `[Eberenz2021]` |
| D7 | `CAL-IMPF-02` | Curvas de agua: forma profundidad-daño **JRC** (NorthAmerica, residential) con **escalar multiplicativo del MDD por estado** como único parámetro libre. | Forma anclada al estándar; un parámetro por estado, simétrico a `v_half`. Transferibilidad: Wagenaar et al. (2018) `[ref?]`. `[Huizinga2017]` |
| D8 | `CAL-WIND-02` | Timestep: **1 h por defecto**, sujeto a test de convergencia (§3.4). Idéntico en calibración y aplicación. | Eberenz interpola a pasos horarios; tutoriales CLIMADA 0.5–1 h. El sesgo de timestep se absorbe en `v_half` → la consistencia domina. La anomalía observada (timesteps finos → pérdidas menores) se investiga por convergencia, nunca se elige por resultado (`OQ-CAL-01`). |
| D9 | `CAL-BAYES-01/02/03` | Escasez de eventos → **jerárquico bayesiano** (partial pooling) en PyMC (réplica Stan opcional), con CLIMADA como forward model vía superficie precomputada (§5). | Conserva detalle estatal; contracción hacia media regional con interpretación física. `BayesianOptimizer` de CLIMADA es optimización, no inferencia. `[GelmanHill2007]` |
| D10 | `CAL-MULTI-01/02` | Combinación multi-peril a nivel **celda** con regla de unión (§6); calibración **conjunta** contra pérdida total. | Cero doble conteo por construcción; cota física daño ≤ valor. Lógica HAZUS viento-inundación `[ref?]`. |
| D11 | `CAL-EXP-02` | Sumas aseguradas estatales desagregadas ∝ LitPop intraestatal. | CNSF da agregados; LitPop es proxy razonable de localización de activos asegurados. Supuesto documentado. `[Eberenz2020LitPop]` |
| D12 | `CAL-OUT-01` | Artefacto canónico: tabla de parámetros versionada + reconstructor determinista. Nunca pickles. | Robustez entre versiones; consumo limpio desde el proyecto paralelo. |
| D13 | `CAL-XWALK-01` | Crosswalk: ciclones con penetración tierra adentro recogen pérdidas de perils "ciclón" **e** "inundación/hidro" en estados del cono de lluvia. | Remanentes ciclónicos en estados interiores (CDMX) se registran bajo inundación en CNSF. |

---

## 3. Datos: inventario y forma requerida

### 3.1 Target de calibración (pérdidas observadas)

**Forma:** DataFrame año × estado (filas = años, columnas = claves INEGI de 2 dígitos), una tabla por ruta (A/B) y por familia de peril (ciclónico agregado; inundación fluvial). Contrato: `DC-CAL-TARGET-4`.

**Reglas del crosswalk** (detalle operativo en `DC-XWALK-1`, `OQ-CAL-02`):
1. Identificar, por año, las tormentas IBTrACS cuyo campo de viento modelado intersecta cada estado con intensidad > `v_thresh`.
2. Para estados del cono de lluvia (intensidad `TCRain` > umbral, aun sin viento dañino), incluirlos en el conjunto afectado del año (D13).
3. La pérdida anual del estado se compara contra el impacto modelado **agregado sobre todas las tormentas del año** — no se particiona la pérdida observada entre tormentas.
4. Años-estado con pérdida > 0 sin tormenta modelada (y viceversa) se flaggean; la regla de inclusión/exclusión se documenta.

**Insumos:** pérdidas CNSF (`MONTO PAGADO`, pipeline existente) · sumas aseguradas CNSF · pérdidas CENAPRED (*Impacto Socioeconómico*, **pendiente scraper**) · INPC (INEGI/Banxico, pinear procedencia) · crosswalk (siguiente entregable).

Ambas series se normalizan a pesos constantes (INPC). La ruta asegurada usa sumas aseguradas *del año del evento* como exposición → consistencia temporal gratis.

### 3.2 Exposición

- `exp_total` = `LitPop.from_countries(['MEX'])` (ruta B, `[Eberenz2020LitPop]`).
- `exp_aseg_{año}` = sumas aseguradas CNSF estatales del año, desagregadas ∝ LitPop intraestatal (ruta A, D11).
- Ambos `GeoDataFrame` con `region_id` = clave INEGI (spatial join con Marco Geoestadístico pineado) y `impf_TC`/`impf_TCSurgeBathtub`/`impf_TR`/`impf_RF` = clave del estado.

### 3.3 Hazard (congelado, una sola vez)

| Hazard | Construcción | Insumos |
|--------|--------------|---------|
| Viento | `TCTracks.from_ibtracs_netcdf(provider='usa', basin=EP+NA)`, filtro ≥ 2000 → `equal_timestep(1.0)` → `TropCyclone.from_tracks(tracks, centroids)` | IBTrACS v04r01. Solo históricas para calibrar. |
| Marejada | `TCSurgeBathtub.from_tc_winds(tc, topo_path)` | DEM `.tif` en mano (procedencia → `OQ-CAL-05`; referencia estándar SRTM15+ V2.0). Relación viento-marejada Xu (2010)/SLOSH con decaimiento tierra adentro. |
| Lluvia ciclónica | `TCRain.from_tracks(...)` (`haz_type='TR'`, mm) | Mismas trayectorias. R-CLIPER vs TCR → `OQ-CAL-03`. |
| Inundación fluvial | `RiverFlood.from_nc(dph, frc)` | `.nc` ISIMIP/CaMa-Flood en mano (procedencia → `OQ-CAL-06`). Máximo anual → consistente con D3. |

**Requisito crítico:** los cuatro hazards comparten los **mismos centroides** (los de la exposición) — sin esto, §6 es imposible. Persistencia: HDF5 + `_procedencia.json`; la calibración corre solo contra hazards congelados (`CAL-GEN-12`).

### 3.4 Test de convergencia de timestep (previo a congelar — D8, `OQ-CAL-01`)

1. 3–4 eventos mayores con buena cobertura de pérdidas (candidatos: Wilma 2005, Odile 2014, Patricia 2015, Willa 2018).
2. `TropCyclone` con timestep ∈ {0.25, 0.5, 1, 3} h sobre la malla definitiva.
3. Comparar (a) swath de intensidad máxima por celda, (b) pérdida agregada por estado con función fija de referencia (Eberenz NA).
4. Documentar la curva de convergencia y la interacción timestep × resolución de centroides (cf. artefacto CDMX del pipeline propio).
5. Congelar donde converge (default esperado 1 h). **Criterio: convergencia, nunca la magnitud del resultado.**

---

## 4. Forma funcional y parámetros

### 4.1 Viento (Emanuel 2011)

$$v_n = \frac{\max(V - V_{thresh},\, 0)}{V_{half} - V_{thresh}}, \qquad f(V) = \frac{v_n^3}{1 + v_n^3}$$

`V_thresh = 25.7` m/s (fijo), `scale = 1` (fijo), `V_half,s` libre por estado. Constructor: `ImpfTropCyclone.from_emanuel_usa(impf_id=s, v_thresh=25.7, v_half=...)`.

### 4.2 Marejada e inundación (JRC profundidad-daño)

Curva base `ImpfRiverFlood.from_jrc_region_sector('NorthAmerica', 'residential')` `[Huizinga2017]`. Parámetro libre: escalar $\kappa_s$ sobre el MDD, recortado tras escalar:

$$MDD_s(d) = \min(\kappa_s \cdot MDD_{JRC}(d),\, 1)$$

Escalares separados $\kappa_s^{surge}$ y $\kappa_s^{RF}$ (agua salada + oleaje vs agua dulce).

### 4.3 Lluvia ciclónica

Sin función estándar en CLIMADA core. Preferencia: sigmoide tipo Emanuel sobre precipitación acumulada con `P_thresh` fijo y `P_half,s` libre — simetría con viento. Fallback: lineal-a-trozos con escalar. Decisión con datos en mano (`OQ-CAL-04`); si no identifica, colapsa al modelo nulo y se reporta.

---

## 5. Modelo jerárquico bayesiano

### 5.1 Por qué no basta `climada.util.calibrate`

Entrega puntos óptimos por minimización (GP search / scipy; costos MSE/MSLE ponderados). Se usa para: calibración nacional de referencia (modelo nulo), diagnósticos (`OutputEvaluator`), verificación de modos posteriores. El partial pooling requiere inferencia completa → PyMC (réplica Stan opcional).

### 5.2 Superficie precomputada (surrogate exacto)

Para hazard y exposición fijos, la pérdida modelada estado-año es monótona y suave en el parámetro libre. Se precomputa con CLIMADA:

- $L_{st}(v_{half})$ sobre malla $v_{half} \in \{30, 32, \ldots, 120\}$ m/s
- $L_{st}(\kappa)$ sobre malla $\kappa \in \{0.1, 0.2, \ldots, 3.0\}$

El likelihood **interpola** (PCHIP monótona) — nunca llama a CLIMADA. Exportación: tensores `(estado, año, malla)` en parquet/NetCDF con procedencia (`DC-CAL-BAYES-1`). Para la calibración conjunta multi-peril, la unión no es separable a nivel agregado → superficie conjunta sobre malla gruesa $(v_{half}, \kappa_{surge}, \kappa_{rain})$ por estado-año, refinada tras corrida exploratoria (`OQ-CAL-10`).

### 5.3 Especificación

Sea $g(s)$ el grupo regional del estado $s$ (Pacífico Sur, Pacífico Norte/Península BC, Golfo, Península de Yucatán, Interior — `OQ-CAL-09`):

$$\mu_g \sim \mathcal{N}(\log \mu_0,\, \sigma_0^2) \quad \text{(} \mu_0 \text{ anclado al } V_{half} \text{ regional NA de Eberenz — prior, no dato)}$$
$$\tau \sim \text{HalfNormal}(\sigma_\tau)$$
$$\log V_{half,s} \sim \mathcal{N}(\mu_{g(s)},\, \tau^2), \qquad \log \kappa_s \sim \mathcal{N}(0,\, \sigma_\kappa^2)$$
$$\log L^{obs}_{st} \sim \mathcal{N}\big(\log L^{mod}_{st}(\theta_s),\, \sigma_{obs}^2\big)$$

Likelihood en log ≈ espíritu MSLE/RMSF (las pérdidas abarcan órdenes de magnitud). Ceros y censura por deducibles: hurdle / censura izquierda, decisión fina con datos (`OQ-CAL-07`).

### 5.4 Validación (`CAL-VAL-01`)

1. Leave-one-year-out sobre años con eventos mayores.
2. Benchmark externo: posterior nacional/regional vs `V_half` NA de Eberenz — el resultado central es la heterogeneidad estatal que el promedio regional esconde.
3. Ruta A vs Ruta B: comparación de rankings estatales de vulnerabilidad.
4. Modelo nulo (Eberenz puro, viento contra total): si la descomposición no mejora out-of-sample, se reporta — eso también es un resultado.
5. Diagnósticos MCMC (R-hat, ESS, divergencias) vía ArviZ; correlaciones posteriores entre bloques como diagnóstico de identificabilidad.

---

## 6. Agregación multi-peril sin doble conteo

**Problema:** las pérdidas observadas año-estado son totales del fenómeno, no separadas por sub-peril. Calibrar cada sub-peril contra el total triplica el conteo; calibrar conjuntamente deja la partición débilmente identificada.

1. **Combinación a nivel celda** (centroides compartidos). Con fracciones de daño por celda-evento:

$$f_{total} = 1 - (1 - f_{viento})(1 - f_{marejada})(1 - f_{lluvia})$$

Regla de unión de daños (lógica HAZUS viento-inundación `[ref?]`): el daño combinado nunca excede el valor del activo; un activo dañado 60% por viento solo puede perder el 40% restante por agua. La suma directa sobreestima sistemáticamente en la costa. Supuesto implícito: independencia condicional de mecanismos dado el evento — documentado; alternativa conservadora $f_{total} = \max(f_i)$ como cota inferior en sensibilidad. CLIMADA no combina entre tipos de hazard nativamente — post-proceso sobre las matrices `imp_mat`.

2. **Un solo likelihood contra el total observado** con los tres bloques de parámetros dentro — cero doble conteo por construcción.

3. **Identificación de la partición:** (i) priors asimétricos — curvas de agua ancladas a JRC (solo escala, centrada en 1); el parámetro libre de verdad es `v_half`; (ii) firma física de los eventos — el panel contiene ciclones de viento extremo/poca lluvia y ciclones débiles en viento/catastróficos en agua; esa variación separa los parámetros. Se reporta la correlación posterior entre bloques; si no identifica, se colapsa al modelo nulo y se reporta.

---

## 7. Flujo de inundación fluvial independiente

1. Hazard `RiverFlood.from_nc()` con los `.nc` en mano (máximo anual → unidad año-estado nativa).
2. Target: pérdidas CNSF de perils de inundación por año-estado, con la regla de partición `CAL-XWALK-02` (hidro → "ciclónica" si hay tormenta en cono de lluvia ese año; "fluvial independiente" si no; mixtos flaggeados) + CENAPRED para ruta B.
3. Función: curva JRC NorthAmerica residencial × $\kappa_s^{RF}$ jerárquico.
4. Fase 2: módulo GloFAS de petals (caudales CDS → footprints por periodo de retorno). Mejor resolución de eventos; mayor costo. Referencia de calibración fluvial del ecosistema CLIMADA/PIK: Sauer et al. (2021) `[ref?]` — confirmar DOI.

---

## 8. Reproducibilidad y exportación

**Artefacto canónico:** `parametros_impacto_estatal.csv` (`DC-CAL-OUT-1`) + `construir_impfset.py` (reconstructor determinista). Downstream consume **la tabla**, nunca pickles. Complementos: hazards/impactos HDF5 + `_procedencia.json`; superficies en parquet/NetCDF; trazas ArviZ NetCDF nombradas por tag de git; `environment.lock.yml` pineado; log de decisiones por corrida (qué años-estado entraron, versión del crosswalk, delta vs corrida anterior). La auditoría de "cómo cambian resultados con cada mejora" = comparación de trazas entre tags.

---

## 9. Limitaciones declaradas

1. **Pluvial/urbana fuera de alcance (fase 1)** — mecanismo dominante en CDMX/Monterrey/Guadalajara; sin hazard nacional off-the-shelf. Mitigación parcial: `TCRain` captura lluvia *ciclónica* en interiores. Futuro: piloto precipitación→daño para CDMX (CHIRPS/ERA5) — requeriría resolución sub-estatal fina.
2. **Hazard de inundación modelado, no observado** — vulnerabilidad condicional a un hazard con error propio.
3. **Ruta asegurada ≠ vulnerabilidad económica total** (penetración, deducibles, demand surge) — por eso D1.
4. **Funciones casadas al hazard CLIMADA con timestep congelado** — no transferibles al pipeline propio sin recalibrar.
5. **Curvas/coeficientes extranjeros como priors** (Eberenz NA, JRC NA, Xu/SLOSH) — el esquema jerárquico los trata como priors actualizables, no como verdad.

---

## 10. Secuencia de trabajo

1. **Crosswalk año-estado ↔ tormentas** (siguiente entregable; requiere el scraper CENAPRED del flujo paralelo).
2. Test de convergencia de timestep → congelar hazards.
3. Exposiciones (LitPop + desagregación CNSF).
4. Tablas target (deflactadas, dos rutas).
5. Calibración nacional de referencia (`climada.util.calibrate`, modelo nulo).
6. Superficies precomputadas → jerárquico PyMC (viento solo).
7. Extensión multi-peril (calibración conjunta).
8. Inundación fluvial independiente.
9. Validación completa y exportación canónica.

---

## Referencias

Las claves resuelven en [[REFERENCES]] (verificadas; `[ref?]` → §99, `OQ-CAL-08`): `[Emanuel2011]` · `[Eberenz2021]` · `[Eberenz2020LitPop]` · `[Huizinga2017]` · `[AznarSiguan2019]` · `[Knapp2010]` · `[IBTrACSv04r01]` · `[Tozer2019]` · `[Tuleya2007]` · `[Lu2018]` · `[GelmanHill2007]` · `[CLIMADAdocs]` · `[PetalsDocs]` · §99: `[Xu2010]`, `[Sauer2021-ref?]`, `[Hazus-ref?]`, `[Wagenaar2018-ref?]`.

---

## Related
[[DECISIONS]] · [[DATA_CONTRACTS]] · [[REFERENCES]] · [[OPEN_QUESTIONS]] · [[CAL_MOC]] · Home: [[_INDEX]]
#arm/cal #type/theory
