# Objetivo ruta B 2000–2023: CENAPRED extendido + tabla de pérdidas

**Pipeline:** `procesar_cenapred.py --crudo` (upstream, sin modificar) → `impactcal.target.cenapred` → `impactcal.target.crosswalk` (v1.1) → `impactcal.target.perdidas` (nuevo) · ejecutado 2026-07-23 UTC · entrega `DC-CAL-TARGET-2` y cierra `OQ-CAL-14` salvo 2024 (`CAL-TARGET-06`).

## Qué entró

Los extensos CENAPRED 2016–2023 y el resumen ejecutivo 2024, capturados a la estructura de la base abierta (24 columnas), con procedencia sha256 por PDF, tabla+página por renglón y conciliación por año contra los totales de control de cada informe (`data/cenapred/pdfs_procesados_2016-2024/`). El panel machine-readable pasa de 2000–2015 a **2000–2024**.

## Por qué la extensión no puede dañar la historia

Los consolidados se regeneraron con el pipeline upstream **sin tocarlo** (ya aceptaba `--crudo`). Antes de confiar en la corrida se re-ejecutó sobre el crudo **original** 2000–2015: los cuatro consolidados reproducen **sha256 idéntico** al de las copias congeladas, así que la invocación es equivalente a la que los produjo y cualquier diferencia posterior viene del dato nuevo, no del montaje. El panel crece 2,833 → 3,723 filas con **0 subtipos `__SIN_MAPEO__`**. Trampa evitada: `procesar_cenapred.py` importa `limpieza_cnsf` por un parche de `sys.path` que **cae en silencio a un stub identidad** si falla — con el stub, `Distrito Federal` no se normaliza a `Ciudad de México` y la entidad 09 se parte en dos series a través de la costura (el mismo modo de fallo que `OQ-CAL-11` señala para CNSF). Se verificó que el import real resuelve antes de correr.

## Qué dice la QA del segmento nuevo (`CAL-GEN-14`)

La pérdida de granularidad es real pero cae **fuera** del grano que consume este proyecto. Desde 2016 CENAPRED ya no publica el registro evento×estado del CENACOM: las filas HIDRO bajan de ~165 a ~65 al año. Sin embargo **la cobertura estatal se mantiene** (22–29 estados con daño en alcance por año, contra 25–32 antes) y, decisivo, **0% del daño en alcance queda sin asignar a un estado** en 2016–2023 (`Varios Estados` = 0.0 MDP todos los años; 2024 tiene 37.1 MDP, 0.3%). Los ciclones conservan grano evento×estado (9.6 filas/año contra 10.4 histórico); lo que se vuelve estado×año es LLUV y compañía, que es exactamente el grano de `CAL-TARGET-02`.

El detector de errores de unidades es la razón MDP/MDD, que debe reproducir el FIX anual: en 2016–2024 lo reproduce **exactamente** (desvío 0.0% en todas las filas señaladas), mientras la base 2000–2015 arrastra varias inconsistencias reales (Chiapas 2003 r=2712 contra 10.84 esperado; Chiapas 2010 r=1293 contra 12.50; Tabasco 2007 con MDD=0). El segmento nuevo es **más limpio que la base que extiende**. Los 10 `error_probable` del segmento nuevo son catástrofes reales, no errores: Tabasco nov-2020 (13,643.8 MDP, conciliado contra la Tabla 2.2 del propio informe), Tula/Hidalgo 2021, Earl 2016 en Puebla/Campeche/Guerrero — el umbral del inspector está calibrado para series estables por hectárea, y un salto de 1000× sobre la mediana del grupo es normal en pérdidas catastróficas.

## Caveats estructurales que viajan al modelo

`INUND` desaparece como subtipo desde 2016 (el daño fluvial se reporta bajo `LLUV`): la partición ciclónica/fluvial sobrevive porque ambos mapean a fluvial, pero no hay desglose de subtipo post-2015. La cola de eventos menores queda **censurada** desde 2016 — no es un cambio real de frecuencia. Y **celda vacía ≠ 0**: la base histórica colapsaba "no dato" a 0 y las filas nuevas los distinguen, lo cual es carga directa para `OQ-CAL-07` (ceros y censura en la verosimilitud). 2017 es genuinamente flaco en hidro (17 estados, 6,013 MDP) porque fue un año dominado por los sismos (GEO 81,698 MDP), no por un hueco de extracción.

## 2024 fuera del panel

`periodo.anio_final: 2023`. El resumen ejecutivo da 6 filas en alcance sobre 5 estados y **ningún estado fluvial con daño**, así que el año no sostiene grano estatal. El crosswalk dejó de derivar `panel_max` del máximo de los datos —que habría metido 2024 en silencio— y ahora respeta la config; además **toda fila más allá del panel se marca `fuera_panel_cenapred` tenga o no pérdida reportada** (19 filas de 2024, 0 filtraciones a ≤2023).

## Crosswalk v1.1 y tabla objetivo

Mismo método, panel más largo: 567 → **678 filas**, solo-hazard 157 → **66** (tormentas que ahora sí encuentran pérdida), eventos CT 167 → **253** con los mismos 2 `sin_match` de 2000. `data/target/perdidas_totales_anual.csv` (`DC-CAL-TARGET-2`): **750 filas, 2000–2023, 32 estados**, en MXN corrientes. La tasa de cobertura se sostiene a través de la costura (ciclónica 7.9 → 7.1 pares/año, fluvial 21.3 → 19.9). `familia_peril` es lo que **reporta** CENAPRED; la reatribución por cono de lluvia de `CAL-XWALK-02` viaja aparte en `familia_xwalk` (82 pares que CENAPRED llama fluviales quedan atribuidos a ciclón), de modo que la máscara de inclusión no re-deriva nada. Falta la columna deflactada: `OQ-CAL-19`.

## Uso

```bash
python procesar_cenapred.py --crudo <base 2000_2024.csv> --cons <dir>   # upstream climateCCR
python -m impactcal.target.cenapred --modo ingerir --forzar
python -m impactcal.target.crosswalk
python -m impactcal.target.perdidas
```

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[OPEN_QUESTIONS]] · [[crosswalk-v1-hazard-side]] · [[Calibracion_Impacto_Mexico_Master]] · Home: [[_INDEX]]
#arm/cal #type/pipeline
