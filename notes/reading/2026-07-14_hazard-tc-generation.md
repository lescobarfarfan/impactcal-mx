# Lectura 2026-07-14 — generación de hazards TC congelados

Qué leer y por qué, por decisión de la sesión ([[hazard-tc-generation]]). Claves en [[REFERENCES]].

Knapp et al. (2010) [Knapp2010] + dataset v04r01 [IBTrACSv04r01]: la descripción del merge multi-agencia de IBTrACS (§ datos y fusión del BAMS) — respalda el universo de tormentas (`CAL-HAZ-SHARED-02`) y explica por qué la vía `provider='usa'` puede traer puntos sin viento/presión, que `estimate_missing=true` completa por relaciones estadísticas.

Eberenz et al. (2021) [Eberenz2021]: §2 (hazard) — el campo de viento **H08** (Holland 2008, default de `TropCyclone.from_tracks`) con tracks históricos IBTrACS `provider='usa'` es exactamente la configuración entregada en `CAL-WIND-01`; releer junto con `CAL-SCOPE-03` (una función calibrada sobre un modelo de viento no es transferible a otro — el sesgo del hazard lo absorbe $v_{half}$).

Tuleya et al. (2007) [Tuleya2007]: evaluación de R-CLIPER en tormentas con landfall en EE.UU. — respalda `haz_rain.h5` v0 (`CAL-RAIN-01`); tener presente su sesgo conocido (subestima acumulados tierra adentro y en tormentas asimétricas), que es justo lo que el trial `OQ-CAL-03` debe pesar.

Lu et al. (2018) [Lu2018]: el modelo TCR físico — la alternativa pendiente del trial `OQ-CAL-03`; leer §2 por los insumos along-track adicionales que TCR exige (viento cortante, humedad), que explican su costo y por qué el default v0 fue R-CLIPER.

## Related
[[CAL_MOC]] · [[hazard-tc-generation]] · [[DECISIONS]] · [[REFERENCES]] · Home: [[_INDEX]]
#arm/cal #type/reading
