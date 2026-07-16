# Huellas fluviales ISIMIP2a congeladas + insumos GloFAS (OQ-CAL-17)

**Pipeline:** `impactcal.hazard.rf` (nuevo) + `impactcal.hazard.glofas --modo auxiliares` (nuevo) · ejecutado 2026-07-16 UTC · manifest `haz_rf_20260716T040216Z` · entrega el segmento ISIMIP2a de `DC-CAL-HAZ-1` (`CAL-RF-02`) y congela los insumos estáticos del pipeline GloFAS (`CAL-RF-03`).

## Qué se generó

**`data/hazard/haz_rf_none.h5`** (2.9 MB) y **`data/hazard/haz_rf_flopros.h5`** (1.5 MB): `RiverFlood` (m de profundidad + fracción inundada) desde las huellas anuales ISIMIP2a congeladas (CaMa-Flood/MATSIRO/GSWP3, máximo anual — consistente con la unidad año×estado, `CAL-TARGET-02`), **años 2000–2010** (11 eventos anuales, `origin=True`), sobre los **100,369 centroides LitPop compartidos** (`CAL-HAZ-SHARED-01`, mapeo celda-a-celda: ambas mallas son de 150 as). Se congelan **ambas variantes de protección** porque la elección en la verosimilitud sigue abierta (`OQ-CAL-16`); la procedencia encadena sha256 de los dos `.nc4` de cada variante y de la exposición. La `frequency` de petals (1/11) se documenta como sin significado — la calibración empata año contra año, nunca usa frecuencias. [WillnerISIMIP2024]

## Verificación

11 eventos × 100,369 centroides por variante, nombres de evento = años 2000–2010; **0 celdas NaN** (todos los centroides caen dentro de la máscara terrestre de CaMa-Flood; el saneador cuenta y anota en procedencia si algún día no fuera así). `none`: ~8,440 celdas inundadas/año, máx 17.98 m (cauces profundos, rango CaMa plausible); `flopros`: ~780 celdas/año, mismo máximo (la protección elimina inundaciones bajo el estándar, no recorta las que lo exceden); profundidad total `none` ≥ `flopros` — coherencia direccional confirmada.

## Insumos GloFAS congelados (paso restante de OQ-CAL-17)

`data/glofas/auxiliares/`: **`flood-maps.nc`** (mapas JRC globales rp10–rp500 fusionados, 257 MB), **`gumbel-fit.nc`** (ajustes Gumbel `loc/scale/samples` a 0.1° de descarga GloFAS 1979–2015, ETH hdl:20.500.11850/641667) y **`FLOPROS_shp_V1`** (estándares de protección — la misma disyuntiva `none`/`flopros` existe en `rf_glofas`, así que `OQ-CAL-16` se decide una sola vez para ambos segmentos). **Trampa detectada y cerrada:** la URL hardcodeada en petals 6.1.0 para `gumbel-fit.nc` devuelve hoy una página HTML (ETH migró su repositorio a DSpace 7) y el downloader de petals la habría congelado sin quejarse; `download_aux` descarga del bitstream re-resuelto **verificando el MD5 del repositorio** (`859e9667…`) y aborta ante cualquier divergencia. Sub-decisión para el cómputo: existe una edición **1979–2023** de los ajustes (hdl:20.500.11850/726304) — nuestra descarga cruda es GloFAS-ERA5 **v4.0**, y la consistencia versión-del-fit ↔ versión-de-descarga debe decidirse en `OQ-CAL-17`. Con esto **todos los insumos de `OQ-CAL-17` están congelados** (crudos 2011–2015 ya estaban); lo que queda es el cómputo: descarga diaria → máximo anual → periodo de retorno (Gumbel) → interpolación de mapas JRC → huella 2011–2015 ×2 protecciones sobre los centroides compartidos, y el **chequeo de consistencia entre segmentos** en años de traslape (ISIMIP2a y GloFAS coexisten 1979–2010) antes de mezclarlos en una sola verosimilitud.

## Decisiones nuevas para `/digest`

(i) **Ambas variantes de protección congeladas como artefactos separados** `haz_rf_{none,flopros}.h5` — `DC-CAL-HAZ-1` nombraba un solo `haz_rf.h5`; el contrato debe reflejar los dos archivos mientras `OQ-CAL-16` siga abierta `[eng]`; (ii) segmento ISIMIP2a = **2000–2010** derivado del eje temporal del nc (no hardcodeado) `[eng]`; (iii) celdas fuera de la máscara CaMa → profundidad 0 documentada (hoy: cero casos) `[eng]`; (iv) `hazard.riverflood.{depth_nc,fraction_nc}` salen de la config — el módulo resuelve ambas variantes por patrón; (v) `DC-CAL-HAZ-1` queda **entregado en sus cuatro perils** (tc, rain, surge, rf×2); el hueco restante es 2011–2015 (GloFAS).

## Uso

```bash
python -m impactcal.hazard.rf [--forzar] [--config RUTA]        # idempotente por variante
python -m impactcal.hazard.glofas --modo auxiliares [--forzar]  # insumos estáticos rf_glofas
```

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[hazard-freeze-inputs]] · [[hazard-surge-generation]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
