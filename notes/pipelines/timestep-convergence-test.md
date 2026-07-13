# Test de convergencia de timestep (OQ-CAL-01)

**Pipeline:** `impactcal.hazard.timestep_test` · **corrida:** `timestep_test_20260713T011309Z` (manifest en `results/manifests/`) · **métricas:** `results/timestep_test/metricas_convergencia_20260713T011309Z.csv` · protocolo: [[Calibracion_Impacto_Mexico_Master]] §3.4, decisión [[DECISIONS]] `CAL-WIND-02`.

**Diseño.** `TropCyclone` para Wilma 2005, Odile 2014, Patricia 2015 y Willa 2018 con timestep $\Delta t \in \{0.25, 0.5, 1, 3\}$ h, sobre **centroides LitPop** (150 y 300 arcsec, patrón `CAL-HAZ-SHARED-01`); referencia = el timestep más fino en la misma malla. Métricas: (a) swath de intensidad máxima por celda (RMSE, sesgo, celdas $> v_{thresh}$), (b) pérdida agregada relativa con función Emanuel **fija** ($v_{half}=74.7$ m/s, solo convergencia — nunca magnitud); estados vía admin-1 Natural Earth (proxy solo-test del Marco Geoestadístico, `DC-CONV-5`).

## Resultados (perdida_rel vs 0.25 h; 150 as ≈ 300 as en todo)

| Evento | 0.5 h | 1 h | 3 h |
|---|---|---|---|
| Wilma 2005 | 0.998 | 0.996 | 0.952 |
| Odile 2014 | 0.989 | 0.926 | 0.799 |
| Willa 2018 | 0.937 | 0.838 | 0.288 |
| Patricia 2015 | 0.940 | 0.771 | 0.300 |

Swath a 0.5 h: RMSE ≤ 2.0 m/s, $|\text{sesgo}|$ ≤ 0.41 m/s; a 1 h el RMSE llega a 4.1 m/s (Patricia). **Grano estatal (lo que esta calibración lee):** a 1 h Patricia captura en Nayarit solo el **17%** de la pérdida de referencia y en Jalisco el 74%; a 0.5 h todos los top-5 estados quedan ≥ 82% (mayoría ≥ 94%).

**Estabilidad de la referencia (check 0.125 h, Patricia+Willa, 300 as):** 0.25 h queda a 2.2% (Patricia) y 3.7% (Willa) de 0.125 h, RMSE < 0.75 m/s — la brecha se contrae ~geométricamente con cada mitad de $\Delta t$, así que 0.25 h es una referencia razonable y el sesgo residual al límite es de pocos puntos porcentuales.

## Interpretación

La pérdida **cae monótonamente** al engrosar $\Delta t$: el máximo por celda sobre posiciones muestreadas del campo Holland solo puede crecer con muestreo más denso — timesteps gruesos *submuestrean* el swath (los huecos estatales de Patricia/Nayarit son celdas que la trayectoria "salta"). La sensibilidad ordena por velocidad de traslación e intensidad (Patricia ≫ Willa > Odile ≫ Wilma). La interacción timestep × resolución es **despreciable** en 150–300 as (métricas casi idénticas): la anomalía "timestep más fino → pérdidas menores" del proyecto origen **no se reproduce aquí** — el signo es el opuesto — y era consistente con su artefacto de discretización a 0.5° (CDMX), no con el timestep.

## Recomendación (para decidir en `/digest`)

1. **Supersede `CAL-WIND-02`: congelar $\Delta t = 0.5$ h** (no el default esperado de 1 h): a 1 h el grano estatal no converge (Nayarit 17%); 0.5 h deja el agregado por tormenta dentro de ~6% y el patrón estatal estable, a 2× el costo de 1 h. Idéntico en calibración y aplicación (el sesgo residual consistente lo absorbe $v_{half}$).
2. **Cerrar `OQ-CAL-01`** con la explicación por submuestreo (la interacción con resolución queda descartada en el rango probado).
3. Pendientes al congelar hazards: re-confirmar 0.5 h vs 0.25 h **en la malla definitiva**; fijar `_procedencia.json` del `IBTrACS.ALL.v04r01.nc` de caché (hoy sin pin, fechado 2025-08-22); San Luis Potosí aparece con pérdida 0 en la referencia de Patricia (ratio NaN) — inocuo, documentado.

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
