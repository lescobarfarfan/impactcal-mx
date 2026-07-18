# 2026-07-18 — Correcciones de magnitud CNSF agrícola (÷1000 y ÷FIX)

Read-log de la sesión que generalizó el outlier Maíz dulce/Sinaloa/2015 a un barrido de toda la
base agrícola, diagnosticó el segundo modo de error (`SUMA ASEGURADA` ≈×FIX, 2022–2024) y aplicó
las 915 correcciones upstream (`CAL-TARGET-05`; caveat en climateCCR
`referencias_riesgo_catastrofico.md` §4, v0.19).

**Banco de México — *Informe Anual 2024*, compilación de cuadros, "Tipos de cambio representativos"** `[BanxicoFIX2024]`. Qué leer: el cuadro de promedios del periodo (serie FIX). Por qué: fija los factores exactos de la corrección ÷FIX (2022 = 20.1274, 2023 = 17.7587, 2024 = 18.3049 MXN/USD) y su límite — el factor real por renglón depende del FIX diario de la fecha de emisión, de ahí el caveat de $\pm 5\text{–}10\%$ en los niveles corregidos 2022–2024. Respaldo directo de `CAL-TARGET-05`.

**climateCCR — `referencias_riesgo_catastrofico.md` §4, recuadro "errores de magnitud en el ramo agrícola" (v0.19)**. Qué leer: el recuadro completo (qué pasa / evidencia / regla / caveat) y el changelog v0.19. Por qué: es la **fuente canónica** de la decisión de corrección — la firma diagnóstica (MXN/ha > 200k con tasa de prima < 0.5\% frente a la mediana histórica de 2.7–7.5\%), la separación en dos vías (÷1000 exacto verificable vs ÷FIX aproximado documentado) y la cola sin resolver (132 renglones de firma débil, atribución a aseguradora imposible desde los archivos públicos). El detalle de evidencia reproducible vive en `scraps/cnsf_agricola_dq/` (barrido, `detalle_suma_inflada_2022_2024.md`).

**CNSF — taller SESA "1era entrega de información — Seguro Agrícola y de Animales" (2008)**. Qué leer: las validaciones de entrega (superficies en hectáreas; siniestrada $\le$ asegurada; superficie $<1$ ha reportada como "1"). Por qué: explica cómo el clúster ×1000 de 2015 pasó las validaciones del sistema — emisión y siniestros se inflaron *coherentemente*, señal de una misma aseguradora reportando unidades erróneas en ambos archivos; también justifica el piso de 10 ha en los chequeos de valor implícito. Sin clave de cita (documento localizado vía espejo no oficial, `scraps/cnsf_outliers_corn_sinaloa/FUENTES_maiz_dulce_sinaloa_2015.md` §A.4); si algo de esto llega al manuscrito, verificar contra la CNSF antes de citar (`CAL-GEN-01`).

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[2026-07-18_inspeccion-datos-qa]] · Home: [[_INDEX]]
#arm/cal #type/reading
