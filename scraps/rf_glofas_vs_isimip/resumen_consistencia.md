# OQ-CAL-17(b) — ¿pueden ISIMIP2a y GloFAS compartir una verosimilitud?

**Respuesta: no como segmentos empalmados. El panel fluvial 2000-2023 debe correrse
con una sola metodología (GloFAS), dejando ISIMIP2a como contraste independiente.**

Reproducir: `IMPACTCAL_DATA_ROOT=<repo>/data python scraps/rf_glofas_vs_isimip/comparar_segmentos.py`
(env CLIMADA). Salidas: `huella_por_anio.csv`, `impacto_estado_anio.csv`,
`impacto_comparado_ancho.csv`.

## Montaje

Ambos segmentos sobre los **mismos centroides** (LitPop 150 as, 100,369 puntos,
`CAL-HAZ-SHARED-01`) y la **misma exposición**, comparados en los 11 años de traslape
(2000-2010, únicos que ambas metodologías cubren). Tres planos, del menos al más
decisivo; el que manda es el tercero, porque es la única capa que ve la verosimilitud.

## 1. Huella cruda — concuerdan

Centroides mojados por año (variante `none`):

| | 2000 | 2003 | 2005 | 2007 | 2010 |
|---|---|---|---|---|---|
| GloFAS | 7,913 | 7,967 | 7,958 | 7,966 | 8,079 |
| ISIMIP2a | 8,034 | 8,374 | 9,032 | 8,660 | 9,536 |

La extensión inundada coincide dentro de ~10%. GloFAS es sistemáticamente algo más
estrecho y **mucho más estable año con año** (7,891-8,079 en once años) que ISIMIP2a
(7,935-9,536).

## 2. Coincidencia espacio-temporal — buena

De los 352 pares estado×año con daño modelado en alguna metodología, **302 (85.8%)
tienen daño en ambas**. Es decir: concuerdan en *dónde* y en *cuándo*.

## 3. Impacto modelado por estado×año — **no concuerdan en nivel**

Pérdida con la curva JRC (`CAL-IMPF-02`) sobre LitPop congelado:

| métrica | valor |
|---|---|
| total GloFAS / total ISIMIP2a | **2.44×** |
| mediana de log10(GloFAS/ISIMIP2a) | +0.25 |
| p10 … p90 de log10(razón) | −1.28 … +1.67 |
| correlación de Pearson | 0.543 |
| correlación de Spearman | 0.618 |

GloFAS entrega sistemáticamente ~2.4× más pérdida modelada, con una dispersión de casi
tres órdenes de magnitud a nivel estado×año. La correlación de rangos (0.62) dice que
ordenan los eventos parecido; el nivel dice que no son intercambiables.

## Por qué eso descarta el empalme

El diseño original partía el panel fluvial en ISIMIP2a (2000-2010) + GloFAS (2011+).
Con una diferencia de nivel de ~2.4× en la frontera, la serie objetivo tendría un
**escalón metodológico en 2010/2011** que la calibración no puede distinguir de un
cambio real de vulnerabilidad: lo absorbería `κ_s^RF` (`CAL-IMPF-02`), sesgando la
función de impacto fluvial entre segmentos y contaminando el contraste ruta A / ruta B.

Por eso la descarga GloFAS se extendió a **2000-2023** y no sólo a los años sin
ISIMIP2a: una sola metodología cubre todo el panel, sin costura, y ISIMIP2a queda
disponible como validación independiente (`CAL-VAL-01`) en lugar de como insumo.

## Advertencias

- La comparación usa la variante de protección `none` en ambos; `OQ-CAL-16`
  (`none` vs `flopros`) sigue abierto y es ortogonal a esto.
- La curva JRC se aplica con un solo `impf_RF` para todos los estados: aquí se comparan
  **hazards**, no se calibra nada.
- Los montos son pérdida modelada, no observada; el ejercicio mide la discrepancia
  entre metodologías de hazard, no el ajuste contra CENAPRED.
- Detectado y corregido en el camino: reutilizar una misma instancia de
  `RiverFloodInundation` entre llamadas a `compute()` corrompe en silencio todos los
  años menos el primero. Con el error, esta misma comparación daba Spearman 0.33 y 62%
  de coincidencia, y habría llevado a concluir que las metodologías son irreconciliables.
  El módulo instancia una por año.

## Related
[[DECISIONS]] · [[OPEN_QUESTIONS]] · [[DATA_CONTRACTS]] · Home: [[_INDEX]]
#arm/cal #type/analysis
