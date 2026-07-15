# Generación de hazards TC: viento y lluvia congelados

**Pipeline:** `impactcal.hazard.tc` (nuevo) · ejecutado 2026-07-15 UTC · manifest `haz_tc_rain_20260715T023857Z` · entrega los dos primeros archivos de `DC-CAL-HAZ-1` y desbloquea el crosswalk v1 (`OQ-CAL-02`).

## Qué se generó

**`data/hazard/haz_tc.h5`** (TropCyclone H08, m/s, 3.6 MB) y **`data/hazard/haz_rain.h5`** (TCRain **R-CLIPER**, mm acumulados por evento, 29 MB), ambos sobre los **100,369 centroides de la exposición LitPop congelada** ([[litpop-exposure]], `CAL-EXP-04`, `CAL-HAZ-SHARED-01`), con `_procedencia.json` encadenando sha256 de exposición y del netCDF IBTrACS. Universo: **540 tormentas IBTrACS EP+NA, temporadas 2000–2024**, con algún punto de trayectoria dentro de `crosswalk.bbox_mexico` (12–35°N, 84–120°W — el mismo bbox del crosswalk v0, una sola definición de "cerca de México"); las 540 cargaron track utilizable (`provider='usa'`, `estimate_missing=true`). Interpolación a **0.5 h congelada** (`CAL-WIND-02`); la caché CLIMADA se verificó hash-idéntica a la copia congelada antes de correr (`CAL-WIND-03`, `impactcal.hazard.tc.ensure_ibtracs_cache`). [Knapp2010][IBTrACSv04r01][Tuleya2007]

## Verificación

Centroides bit-idénticos a la exposición congelada en ambos archivos; 540 eventos 2000–2024; **163 eventos con viento >17.5 m/s sobre la malla** (~6.5/año, plausible). Spot-checks (máximo sobre celdas, todas terrestres): Patricia 66.1 m/s, Wilma 58.8 m/s, Odile 55.7 m/s, Willa 42.4 m/s; lluvia Wilma 540.8 mm (consistente con su récord sobre Quintana Roo), Willa 222.2 mm. **Determinismo confirmado:** una corrida smoke independiente (2 tormentas, data-root temporal) reprodujo exactamente los mismos máximos.

## Decisiones nuevas para `/digest`

(i) **Universo del hazard** = filtro bbox near-Mexico sobre EP+NA ≥2000 (una tormenta sin punto en el bbox no puede producir viento >25.7 m/s ni lluvia R-CLIPER — radio máx. 300 km — sobre territorio) `[eng]`; (ii) **`temporada_max: 2024`** — última temporada completa del nc congelado `[eng]`; (iii) **`estimate_missing: true`** — evita huecos artificiales tipo "pérdida>0 / sin tormenta modelada" en el crosswalk `[eng]`; (iv) **lluvia v0 = R-CLIPER** (default petals; si `OQ-CAL-03` elige TCR se regenera solo `haz_rain.h5` — borrar el `.h5` y re-correr, el viento no se toca); (v) `DC-CAL-HAZ-1` pasa a **parcialmente entregado** (tc + rain ✓; surge + rf pendientes); `OQ-CAL-02` queda desbloqueado.

## Uso

```bash
python -m impactcal.hazard.tc [--forzar] [--config RUTA]   # idempotente por artefacto
```

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[hazard-freeze-inputs]] · [[litpop-exposure]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
