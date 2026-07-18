# Anomalía 2022–2024: SUMA ASEGURADA inflada (≈×FIX) — evidencia y contraste con 2015

Investigación exploratoria (2026-07-18), **fuera del canon**. Complementa `resumen_hallazgos.md`;
responde "¿en qué difiere la anomalía Sinaloa 2022–2024 de la de 2015?". Reproducible con los
consolidados CNSF agrícolas del repo hermano climateCCR.

## 1. Sinaloa, Maíz dulce — el mismo par celda, dos errores distintos

| Diagnóstico | 2015 | 2022–2024 |
|---|---|---|
| Campo corrupto | **SUPERFICIE** (emisión y siniestros) | **SUMA ASEGURADA** (solo emisión) |
| Superficie | 6,104,409 ha (mediana resto: ~620 ha) | 477–889 ha — **normal** |
| MXN/ha implícito | 41 (demasiado **bajo**) | 496k / 933k / 775k (demasiado **alto**; histórico 14k–45k) |
| Prima emitida | normal en MXN (0.8–3× mediana) | normal en MXN por ha (365–2,631 MXN/ha vs 358–1,667 histórico) |
| Tasa de prima (prima/suma) | 0.80% (baja porque la suma también subió ~×14 con 61 pólizas) | **colapsa a 0.07–0.34%** vs 1.4–5.5% histórico de la celda |
| Factor de inflación | **×1000 exacto** (÷1000 devuelve 52,673 y 21,834 MXN/ha, rango 2014/2016) | **≈×FIX del año**: ÷20.13 (2022) → 24,657; ÷17.76 (2023) → 52,543; ÷18.33 (2024) → 42,253 MXN/ha — los tres dentro del rango histórico 24k–53k |
| Lado siniestros | inflado coherentemente (3.8M ha; pasa la validación SESA siniestrada≤asegurada) | sin siniestros en la celda 2022–2024; no aparenta afectación |
| Control interno mismo año | todo el ramo/celda afectado | **solo el esquema "Seguro agrícola a la inversión"**; renglones hermanos del mismo año normales (2022 daños directo: 30.5k/ha; 2024 ajuste al rendimiento: 65k/ha; mixto: 35k/ha) |

FIX promedio anual aproximado (Banxico, por confirmar contra serie SF43718): 2022 ≈ 20.13,
2023 ≈ 17.76, 2024 ≈ 18.33 MXN/USD.

## 2. No es Sinaloa: es sistémico desde 2022

Firma "suma inflada" a nivel renglón (base agrícola Nacional, sup ≥ 10 ha): MXN/ha > 200k
**y** tasa de prima < 0.5% **y** prima > 0:

- Renglones por año: ≤9 (2008–2019) · 21 (2020) · 26 (2021) · **224 (2022) · 211 (2023) · 196 (2024)**.
- 2022+ por entidad: Sonora 117, Sinaloa 78, Veracruz 54, Jalisco 54, Chihuahua 53, Guanajuato 49,
  Michoacán 44, … (≥12 entidades).
- 2022+ por esquema: "Seguro agrícola a la inversión" 420 · "…a la inversión por planta" 185 ·
  resto 26.
- Explica **426 de los 839** hallazgos `B2_valor_implicito_alto` del barrido (los pre-2022 son
  mayormente cola legítima de cultivos de alto valor).

### Subgrupo "a la inversión" (420 renglones): factor ≈ FIX, no ×100 ni ×1000

- ÷FIX del año → **84.3%** cae en banda plausible [15k, 200k] MXN/ha; ÷100 → solo 18.1%.
- Tasa de prima implícita tras ÷FIX: **mediana 3.12%** — indistinguible de la mediana histórica
  del mercado (3.9–5.4% en 2008–2021). Tras ÷100 sería 16.8% (implausible).
- Hipótesis: montos capturados en MXN pero procesados como USD y convertidos otra vez a MXN
  (doble conversión) en la entrega SESA de una o más aseguradoras, a partir del ejercicio 2022.
  El consolidado no trae columna de aseguradora, así que no es atribuible desde estos archivos.

### Subgrupo "por planta" (185 renglones): además, UNIDADES ASEGURADAS = 0

- Todos los renglones por-planta 2022+ traen **0 unidades** (pre-2022 el esquema existía con
  MXN/ha mediana de 28.9k — normal). Sin conteo de plantas no hay cross-check natural.
- Los extremos (arándano Jalisco 29.1B MXN / 391 ha = 74M MXN/ha; agave, piña) quedan altos aun
  ÷FIX (~3.7M/ha) — factor heterogéneo, posiblemente error adicional. Mediana de tasa 0.31% →
  ÷FIX implica ~6%: plausible para la mayoría, no para los extremos.
- Detalle suelto: un renglón arándano 2023 con **prima negativa** (endoso/cancelación; ya
  contado en `A4_valores_negativos`).

## 3. Implicación para la decisión

- Las **113 correcciones ÷1000** propuestas (patrón 2015) son de factor exacto y verificable:
  restauran el MXN/ha al rango del propio historial de cada celda y la coherencia
  emisión↔siniestros. Riesgo bajo.
- La anomalía 2022–2024 **no admite corrección mecánica análoga**: el factor es ≈FIX (varía por
  año y por fecha de emisión intra-año) y en por-planta es heterogéneo. Opciones: (a) excluir/
  marcar los renglones con la firma en las vistas del dashboard; (b) corregir ÷FIX promedio
  anual como aproximación documentada; (c) verificación externa (CNSF/aseguradora) antes de
  corregir. La firma es filtrable: `MXN/ha > 200k & tasa < 0.5%` (+ `anio ≥ 2022`).

## 4. Resolución (2026-07-18): correcciones aplicadas en climateCCR

Aprobado por el usuario y aplicado el mismo día. **915 correcciones** en copia
(`emision_corregida.csv` / `siniestros_corregida.csv` + auditoría `_correcciones_dq.csv`,
originales intactos), codificadas en `limpieza_cnsf.py` §6 y aplicadas por
`corregir_consolidados_agricola.py`:

- **÷1000 superficies**: 25 renglones emisión + 97 siniestros (regla extendida: monto/ha
  imposiblemente bajo sin piso, y monto 0 con superficie >10× la asegurada corregida de la
  celda — captura Sinaloa maíz dulce siniestros 2015, Guanajuato trigo/espárrago, Nayarit
  arroz 540k ha).
- **÷FIX sumas 2022–2024**: 793 renglones (631 por firma tasa<0.5% + 162 por ≥5× la mediana
  histórica propia con prima≤0). FIX promedio del periodo, Banxico (Informe Anual,
  compilación 2024): 20.1274 / 17.7587 / 18.3049. **132 renglones de firma débil sin
  corregir** (revisión manual pendiente).

Verificación: re-barrido sobre las copias corregidas → `B1_superficie_mayor_al_estado` 11→0,
`B2_alto` 2022+ 426→251 (los restantes = firma débil no corregida + celdas legítimas de alto
valor), Sinaloa maíz dulce sin flags críticos (solo nota estadística B5 por el año grande
2015, ya plausible: 6,885 ha, 61 pólizas, 41k MXN/ha). Caveat de interpretación completo:
climateCCR `referencias_riesgo_catastrofico.md` §4, recuadro agrícola (changelog v0.19).

## Related
[[resumen_hallazgos]] · `scraps/cnsf_outliers_corn_sinaloa/FUENTES_maiz_dulce_sinaloa_2015.md`
#arm/cal #type/scrap
