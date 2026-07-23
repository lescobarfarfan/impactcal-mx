# Panel fluvial GloFAS 2000–2023 (cierra OQ-CAL-17)

**Pipeline:** `impactcal.hazard.rf_glofas` (nuevo) + `impactcal.hazard.glofas --modo descargar` · ejecutado 2026-07-23 UTC · entrega el insumo fluvial de la verosimilitud (`CAL-RF-03/04`, `DC-CAL-HAZ-1`) y cierra `OQ-CAL-17` en sus tres partes.

## Qué se generó

**`data/hazard/haz_rf_glofas_{none,flopros}.h5`**: `Hazard` `RF` (m de profundidad + fracción inundada) con **24 eventos anuales 2000–2023** sobre los **100,369 centroides LitPop compartidos** (`CAL-HAZ-SHARED-01`), 8,594 y 7,752 centroides con agua respectivamente. La cadena es la de petals `rf_glofas`: descarga diaria `dis24` → **máximo anual** → periodo de retorno contra el ajuste Gumbel → regrid a la malla de mapas JRC → protección → profundidad por interpolación de los mapas. El máximo anual se toma **antes** del periodo de retorno, para que la resolución temporal sea la misma que la del segmento ISIMIP2a (`CAL-RF-01`) y la de la unidad año×estado (`CAL-TARGET-02`). La `frequency` de petals se documenta como sin significado: son eventos anuales observados. [Harrigan2020]

**`data/glofas/crudos/`**: 24 NetCDF anuales (981 MB, GloFAS-ERA5 v4.0, bbox México), los 24 verifican sha256. Se descargó **todo el panel** y no sólo los años sin ISIMIP2a porque los años de traslape son el insumo del chequeo de consistencia que `OQ-CAL-17(b)` exigía — y una vez hecho ese chequeo, son también los que permiten una serie de metodología única (`CAL-RF-04`).

## Tres trampas silenciosas

**(i) Convención de longitud.** Los NetCDF GloFAS traen longitud en **0–360** (242.025…273.975) mientras el ajuste Gumbel y los mapas JRC usan −180..180. Sin convertir, el reindexado no encuentra ninguna celda. Se convierte antes que nada.

**(ii) Edición del ajuste Gumbel (`OQ-CAL-17c`, decidido con datos).** `transform_ops.return_period` reindexa el fit sobre las coordenadas de la descarga con **tolerancia 1e-3°** y `assert_no_fill_value`. La edición 1979–2015 que petals referencia vive en la malla GloFAS **v3 de 0.1°** y nuestra descarga congelada es **v4.0 de 0.05°**, así que falla en voz alta (`Reindexing 'loc' to 'dis24' exceeds tolerance`). Se fija la edición **1979–2023** (hdl:20.500.11850/726304, 101 MB vs 10 MB = 4× celdas, malla 0.05°), que además es la consistente en versión con la descarga. [GumbelGloFAS-ref?]

**(iii) Cache contaminado entre años.** Reutilizar una misma instancia de `RiverFloodInundation` entre llamadas sucesivas a `compute()` **corrompe en silencio todos los años menos el primero** — sus intermedios cacheados se filtran. Medido con instancia fresca vs reusada: 2001 pasa de 197,091 a 5,772 celdas finas mojadas, 2002 de 198,490 a 7,266. Una sola llamada con los tres años juntos reproduce la columna correcta, así que el error está en el reuso y no en los datos (las descargas son homogéneas: 365/366 pasos, máximos anuales comparables, y 2000 ni siquiera es el año más húmedo). **El módulo instancia una `RiverFloodInundation` por año.** Se detectó porque GloFAS 2000 daba 20× más celdas mojadas que 2001 mientras la descarga cruda decía que 2000 fue el año más seco.

## Agregación a los centroides

La malla JRC es de **30 as** y los centroides LitPop de **150 as**: exactamente 5× más gruesos, 25 subceldas por centroide. Se agrega como ISIMIP2a reporta su par flddph/fldfrc: `intensity` = **profundidad media de las subceldas mojadas** (no sobre las 25 — la profundidad es la que hay *donde* inunda) y `fraction` = **subceldas mojadas / subceldas totales**. Las celdas sin cobertura de mapa JRC (NaN, ≈97% del bbox: no son llanura de inundación) cuentan como secas. La reducción ocurre año por año, así que la malla fina nunca se acumula — con 24 años de golpe serían ~1.7 GB de rejilla viva.

## Verificación

24 eventos × 100,369 centroides por variante; nombres de evento = años; mismos centroides que `haz_tc.h5`/`haz_rain.h5`/`haz_surge.h5`/`haz_rf_*.h5`, de modo que la combinación multi-peril a nivel celda (`CAL-MULTI-01`) sigue siendo válida por construcción. `none` ≫ `flopros` en centroides con agua, dirección coherente con la protección. Contra ISIMIP2a en los 11 años de traslape: extensión inundada dentro de ~10% y mucho más estable año con año — ver [[hazard-rf-isimip]] y el análisis de consistencia (`scraps/rf_glofas_vs_isimip/`).

## Uso

```bash
python -m impactcal.hazard.glofas --modo descargar   # idempotente por año
python -m impactcal.hazard.rf_glofas [--forzar]      # idempotente por variante
python scraps/rf_glofas_vs_isimip/comparar_segmentos.py   # chequeo OQ-CAL-17(b)
```

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[hazard-rf-isimip]] · [[hazard-freeze-inputs]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
