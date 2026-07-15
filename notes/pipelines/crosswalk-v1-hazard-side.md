# Crosswalk v1: conjunto afectado lado-hazard

**Pipelines:** `impactcal.hazard.footprints` (nuevo) + `impactcal.target.crosswalk` (v0→v1) · ejecutados 2026-07-15 UTC · manifests `huellas_estatales_20260715T030316Z`, `crosswalk_v1.0-huellas-hazard_*` · resuelve el grueso de `OQ-CAL-02` ([[hazard-tc-generation]] lo desbloqueó).

## Qué cambió de v0 a v1

**Conjunto afectado lado-hazard (`CAL-XWALK-01`).** `data/crosswalk/huellas_estatales.csv` (2,451 pares evento×estado con intensidad >0) tabula el máximo estatal de los hazards congelados; de ahí `sids_viento` = tormentas con viento >$v_{thresh}=25.7$ m/s sobre el estado (167 pares, 86 tormentas) y `sids_cono_lluvia` = tormentas con lluvia R-CLIPER >**50 mm** (625 pares). La tabla v1 (`v1.0-huellas-hazard`) tiene **567 filas año×estado**: 410 con eventos CENAPRED + 157 solo-hazard (30 en el panel, flag `tormenta_sin_perdida`; 127 post-2015, `fuera_panel_cenapred`).

**Umbral del cono = 50 mm `[eng]`, decidido 2026-07-14** con sensibilidad 50/80/100/150: el cono define *pertenencia*, no daño — el filtro de daño lo pone `P_thresh` de la función de lluvia (`CAL-IMPF-03`) — así que domina minimizar pérdidas CT sin tormenta modelada (21 vs 72 a 150 mm); las familias son estables al umbral (fluvial 249→274 en el rango).

**Familia v1 (`CAL-XWALK-02`).** Un evento LLUV/INUND es ciclónico si el cono de una tormenta alcanza el estado ese año **y** la ventana del evento solapa la de esa tormenta (±3 días) — reemplaza el proxy v0 de ventanas nacionales, que sobre-atribuía: de las 220 `mixta_flag` v0, 123 se resuelven (114→fluvial, 6→ciclónica a 50 mm, resto se re-particiona); quedan **114 mixtas**. Familias v1: 249 fluvial, 47 ciclónica, 114 mixta.

**Cola de revisión v0 → v1.** Los 68 empates por fecha con candidatos múltiples bajan a **17** (51 desambiguados exigiendo que la huella del candidato toque el estado del evento; 8 quedan `candidatos_sin_huella` = ningún candidato toca). Fuzzy conservador (difflib ≥0.8, único en la temporada) resuelve **2 typos** de CENAPRED (`nombre_fuzzy`); los **2 `sin_match` de 2000** son eventos sin nombre (uno además sin fechas) — exclusión documentada. **21 año-estado CT sin tormenta modelada** (`perdida_sin_tormenta_modelada`): mayormente estados interiores con remanentes que las trayectorias/huellas IBTrACS no alcanzan — cola de inclusión/exclusión documentada de `CAL-XWALK-01`.

## Para `/digest`

(i) umbral cono 50 mm `[eng]` (supersede parcial `CAL-XWALK-03/04`: v1 entregado, regla de familia cono∧ventana); (ii) `DC-XWALK-1`: semántica v1 — `familia_asignada` vacía en filas solo-hazard, flags nuevos (`tormenta_sin_perdida`, `fuera_panel_cenapred`, `perdida_sin_tormenta_modelada`, `candidatos_filtrados_huella`, `candidatos_sin_huella`, `nombre_fuzzy`); (iii) `OQ-CAL-02`: cerrar o reducir a la cola residual (17+8 candidatos, 21 sin-tormenta, 114 mixtas — material del run decision log de calibración).

## Uso

```bash
python -m impactcal.hazard.footprints [--forzar]   # huellas (CLIMADA env)
python -m impactcal.target.crosswalk               # v1 (pandas puro)
```

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[hazard-tc-generation]] · [[2026-07-12_crosswalk-v0-cenapred]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
