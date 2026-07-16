# Generación del hazard de marejada: haz_surge congelado

**Pipeline:** `impactcal.hazard.surge` (nuevo) + re-congelado del DEM en `impactcal.hazard.freeze_inputs` · ejecutado 2026-07-16 UTC · manifest `haz_surge_20260716T040138Z` · entrega el tercer archivo de `DC-CAL-HAZ-1` y cierra el caveat costero de `CAL-SURGE-02`.

## El caveat costero, resuelto

El chequeo previo de `CAL-SURGE-02` resultó **positivo**: con el recorte exacto v0 del DEM, **251 de 20,418 centroides costeros con viento** muestreaban nodata — y `TCSurgeBathtub.from_tc_winds` (petals) **descarta en silencio** todo centroide cuya elevación muestreada no cumple `0 ≤ h ≤ 10 m` (el muestreo bilineal convierte nodata en `NaN`, que falla ambas comparaciones). Dos causas, ninguna curable con buffer del polígono: (i) **lagunas costeras** interiores a la línea de costa pero exteriores al polígono 00ent (Ojo de Liebre, Términos), y (ii) **huecos nodata del propio raster origen** (`SRTM15+V2.tiff` pineado no es el producto SRTM15+ puro — trae huecos dispersos, p. ej. Isla Clarión). Solución en `freeze_dem`: **recorte rectangular al bbox** del polígono nacional con buffer (`hazard.dem_buffer_grados: 0.1`) **sin máscara** — conserva topo-batimetría real en todo el litoral — más **relleno por interpolación de vecinos** (`rasterio.fill.fillnodata`) de los 16,325 huecos del origen (0.048% de la ventana), con postcondición dura de cero nodata. Chequeo final: **nan=0**; 3,666 centroides elegibles para surge (152 más que los que sobrevivían al descarte silencioso); 254 bajo nivel del mar quedan excluidos por diseño de petals. El DEM congelado pasa de 19 MB (máscara exacta) a 54 MB (bbox). [Tozer2019]

## Qué se generó

**`data/hazard/haz_surge.h5`** (TCSurgeBathtub, m, 1.4 MB): relación viento-marejada de Xu (2010) — `surge = 0.1023·max(v−26.8224, 0) + 1.8288` — menos elevación del terreno, con decaimiento tierra adentro **0.2 m/km** (default petals, Pielke & Pielke 1997) y sin ajuste de nivel del mar (calibración histórica); `fraction` = fracción de celda sobre tierra según el DEM de 15 as. Eventos, fechas y centroides **heredados de `haz_tc.h5`** — `CAL-HAZ-SHARED-01/02` se cumplen por construcción; la procedencia encadena sha256 de `haz_tc.h5` y del DEM. El chequeo costero corre dentro del pipeline y **aborta ante cualquier nodata**. [Xu2010]

## Verificación

540 eventos × 100,369 centroides; **79 eventos con marejada >0** (solo tormentas fuertes tocando costa superan el umbral efectivo de ~26.8 m/s cerca del litoral — plausible); máximo 5.79 m (rango físico TC); `fraction` ∈ [0,1].

## Decisiones nuevas para `/digest`

(i) **`CAL-SURGE-02` se supersede**: DEM congelado = recorte bbox + fillnodata de huecos del origen, caveat cerrado con chequeo automático dentro de `impactcal.hazard.surge` `[eng]`; (ii) parámetros surge **fijos en defaults petals** (decaimiento 0.2 m/km, SLR 0) `[eng]`; (iii) `fuentes_externas.dem_mexico` (recorte notebook v0) sale de la config — la derivación ahora es in-repo desde el global pineado; (iv) `DC-CAL-HAZ-1`: tc + rain + **surge ✓**; falta rf → ver [[hazard-rf-isimip]].

## Uso

```bash
python -m impactcal.hazard.surge [--forzar] [--config RUTA]   # idempotente
# re-derivar el DEM: borrar data/dem/SRTM15+V2_Mexico.tif* y correr freeze_inputs
```

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[hazard-freeze-inputs]] · [[hazard-tc-generation]] · [[hazard-rf-isimip]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
