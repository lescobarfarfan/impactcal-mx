# Outlier CNSF agrícola — Maíz dulce, Sinaloa 2015: hallazgos y fuentes candidatas

Investigación exploratoria (2026-07-17), **fuera del canon** del proyecto. Datos: consolidados
CNSF agrícola (`climateCCR/data/hazard_mx/datos_CNSF/consolidados/agricola_y_animales/`),
verificados contra el crudo `2015 Agricola Bases.xlsx`. Código y figuras en esta carpeta
(`analisis_maiz_dulce.py`).

## 1. Qué se verificó (hechos, reproducibles con el script)

- **Emisión, Sinaloa, Maíz dulce 2015: 6,104,408.89 ha aseguradas** vs mediana de 621.5 ha en
  los demás años (ratio ~9,822×; z-robusta ~24,289). El salto vive en el crudo de la CNSF, no
  lo introdujo la consolidación: son 2 de 3 renglones del Excel original (2,924,552.05 ha y
  3,179,075.64 ha, ciclo Primavera-Verano; el tercer renglón, Otoño-Invierno, trae 781.20 ha
  normales).
- **Siniestros, Sinaloa, Maíz dulce 2015: 3,809,613.06 ha siniestradas** vs mediana de 72 ha
  (ratio ~52,911×). Casi todo bajo causa "Huracán, Ciclón, Tornado, Vientos Fuertes"
  (3,809,472 ha) con **monto pagado de apenas 49,942.76 MXN**.
- **Los montos monetarios NO saltan**: prima emitida 2015 = 3× la mediana, monto pagado = 12×.
  La corrupción está exclusivamente en los campos de superficie.
- **Valor asegurado implícito** (suma asegurada / superficie): ~25–53 MXN/ha en 2015 vs
  14,000–45,000 MXN/ha en 2009–2021. Dividir la superficie entre 1,000 devuelve los renglones
  exactamente al rango plausible (~52,673 y ~21,834 MXN/ha) → **error de magnitud ×1,000**, no
  evento real.
- **Imposibilidad física**: 6.1 M ha ≈ 5× toda la superficie sembrada de Sinaloa (~1.2 M ha) y
  ~4× la superficie asegurada nacional (~1.5 M ha en 2014, ver fuente B.1). El maíz dulce es un
  cultivo de nicho (cientos a pocos miles de ha en Sinaloa/Sonora).
- **No es exclusivo de maíz dulce**: el barrido de toda la base (ver
  `celdas_superficie_mayor_200k_ha.csv`) muestra un clúster de celdas imposibles concentrado en
  2015 — Michoacán-aguacate 13.9 M ha, Guanajuato-cebolla 4.3 M ha, Sonora-sandía 3.3 M ha,
  Guanajuato-espárrago 3.2 M ha, Sonora-pepino 2.8 M ha — con ecos en 2016–2018 (Michoacán-
  aguacate 9.7 M; CDMX-"otro cultivo" 5.1 M). En maíz dulce, Guanajuato (116,000 ha) y SLP
  (144,999.92 ha) también son imposibles en 2015.
- Consistencia reveladora: la validación del SESA exige superficie siniestrada ≤ superficie
  asegurada (fuente A.4), y los renglones inflados la cumplen (3.8 M < 6.1 M) — emisión y
  siniestros se inflaron **coherentemente**, lo que apunta a una misma aseguradora reportando
  unidades erróneas en ambos archivos, pasando las validaciones internas del sistema.

**Hipótesis de trabajo:** error de captura/unidades (~×1,000) de una o más aseguradoras en la
entrega estadística SESA del ramo agrícola 2015 (quizá superficie reportada en m² parciales,
miles mal escalados o un campo monetario volcado en la columna de superficie), que la CNSF
publica "as reported". No hay fe de erratas pública conocida (búsqueda 2026-07-17 sin
resultados). Los siniestros "reales" de maíz dulce Sinaloa 2015 fueron chicos: heladas de enero
2015 (104 ha, 782,662 MXN pagados) + un evento de viento/lluvia menor.

## 2. Fuentes candidatas para explicar/documentar el punto anómalo

### A. CNSF / regulatorio (¿errata, metodología, formatos de entrega?)

1. CNSF — Información estadística de instituciones y sociedades mutualistas (bases SESA por
   ramo, incluido agrícola y de animales):
   <https://www.cnsf.gob.mx/EntidadesSupervisadas/InstitucionesSociedadesMutualistas/Paginas/InformacionEstadistica.aspx>
2. CNSF — Portal de datos abiertos (datasets publicados y sus notas):
   <https://www.cnsf.gob.mx/Transparencia/Paginas/DatosAbiertos.aspx> y
   <https://www.datos.gob.mx/organization/cnsf>
3. CNSF — Sistemas de entrega de información estadística (SESA/RR-8, manuales):
   <https://www.cnsf.gob.mx/Sistemas/Paginas/InformacionEstadistica.aspx>
4. Taller SESA "1era entrega de información — Seguro Agrícola y de Animales" (documento CNSF,
   2008; define formatos texto con separadores, unidades en hectáreas, y validaciones — p.ej.
   superficie <1 ha se reporta como "1", siniestrada ≤ asegurada):
   <https://silo.tips/download/taller-de-la-1era-entrega-de-informacion-seguro-agricola-y-animales-sistema-esta>
5. CUSF interactiva (Circular Única de Seguros y Fianzas, anexos de reportes regulatorios;
   marco vigente desde la LISF, abril 2015 — año del outlier, posible quiebre de régimen de
   reporte): <https://lisfcusf.cnsf.gob.mx/CUSF/CUSF38_1>
6. Vía de confirmación directa: solicitud de acceso a la información (PNT/INAI) a la CNSF
   preguntando por revisiones/erratas de la base SESA agrícola 2015 y por la aseguradora
   reportante de los renglones de maíz dulce Sinaloa. *(Acción, no fuente; sin URL.)*

### B. Sector asegurador agropecuario (dimensionar lo plausible)

1. SADER — "AGROASEMEX, protegiendo al sector rural" (menciona ~1.5 M ha aseguradas en 2014;
   cifra por confirmar contra informe anual):
   <https://www.gob.mx/agricultura/articulos/agroasemex-protegiendo-al-sector-rural>
2. CEPAL — *El seguro agropecuario en México: experiencias recientes* (panorama institucional
   y órdenes de magnitud del aseguramiento):
   <https://repositorio.cepal.org/server/api/core/bitstreams/768d0fc2-40b0-4d3b-9ef2-98479f77093b/content>
3. DOF — Reglas de Operación del Programa de Aseguramiento Agropecuario (SHCP, 27-dic-2015;
   contexto del esquema de subsidio a la prima en el año del outlier):
   <https://www.dof.gob.mx/nota_detalle.php?codigo=5421430&fecha=27/12/2015>
4. AGROASEMEX — datasets de reaseguro en datos.gob.mx (contraste independiente de superficies):
   <https://www.datos.gob.mx/dataset/reaseguros_agroasemex>

### C. Verdad de campo agrícola (¿cuánto maíz dulce existe realmente?)

1. SIAP/SADER — Anuario estadístico de la producción agrícola ("cierre agrícola"; consultar
   cultivo "Maíz dulce", Sinaloa, 2014–2016 — superficie sembrada/cosechada real):
   <https://nube.agricultura.gob.mx/cierre_agricola/>
2. SIAP/SADER — Avance de siembras y cosechas: <https://nube.agricultura.gob.mx/avance_agricola/>
3. Gobierno de Sinaloa — indicadores de agricultura (superficies estatales por cultivo):
   <https://estadisticas.sinaloa.gob.mx/eBooks/Temas/AGRICULTURA2023.pdf>
4. CODESIN — reportes "Sinaloa en Números" de agricultura (superficie total estatal ~1.2 M ha,
   contra la cual 6.1 M ha es imposible):
   <https://sinaloaennumeros.codesin.mx/wp-content/uploads/2023/06/Reporte-24-del-2023-de-Agricultura-en-sinaloa-2022.pdf>

### D. Registro de eventos 2015 (¿hubo evento real que lo justifique? — No a esta escala)

1. CENAPRED — *Impacto socioeconómico de los desastres en México 2015* (registro oficial de
   daños por evento/estado; consultar capítulo hidrometeorológico, sección Sinaloa; PDF grande,
   no revisado aquí):
   <https://www1.cenapred.unam.mx/es/Publicaciones/archivos/382-IMPACTOSOCIOECONMICO2015.pdf>
2. SADER Sinaloa — heladas enero 2015: ~25,480 ha dañadas (15,400 de maíz) de 676,000
   establecidas; el evento real del ciclo OI 2014-15:
   <https://www.gob.mx/agricultura%7Csinaloa/articulos/baja-afectacion-a-cultivos-por-heladas-en-sinaloa> y
   <https://www.gob.mx/agricultura%7Csinaloa/articulos/sube-a-12-mil-hectareas-siniestradas-totalmente-por-las-heladas>
3. DOF 30-sep-2015 — boletín/aviso de emergencia por lluvia severa e inundación fluvial y
   pluvial del 11–12 de septiembre de 2015 en Mazatlán, Sinaloa (candidato al origen "real" de
   los siniestros por viento/lluvia del ciclo PV; escala local, no millones de ha):
   <https://finanzas.tamaulipas.gob.mx/uploads/2015/09/DOF_30_SEPT_2015.pdf>
4. NHC — Tropical Cyclone Report, Hurricane Patricia (oct-2015; impactó Jalisco/Colima/Nayarit,
   no Sinaloa): <https://www.nhc.noaa.gov/data/tcr/EP202015_Patricia.pdf>
5. SMN/CONAGUA — reseña del huracán Patricia 2015:
   <https://smn.conagua.gob.mx/tools/DATA/Ciclones%20Tropicales/Ciclones/2015-Patricia%20.pdf>
6. Temporada de huracanes del Pacífico 2015 (visión de conjunto; Sandra, nov-2015, se disipó
   antes de tocar Sinaloa): <https://es.wikipedia.org/wiki/Hurac%C3%A1n_Sandra>

### E. Qué falta / siguientes pasos si esto escala al canon

- Ninguna de las fuentes halladas documenta el outlier explícitamente: **no existe (o no es
  pública) una fe de erratas de la CNSF** para la base agrícola 2015. La confirmación fuerte
  requiere A.6 (solicitud INAI) o contraste con el anuario impreso CNSF 2015.
- Si el ramo agrícola llegara a usarse en `impactcal-mx` (hoy fuera de alcance), la regla
  práctica sería: filtrar celdas con superficie > superficie sembrada estatal (SIAP) o con
  valor implícito MXN/ha fuera de [1,000, 200,000], y documentar la decisión con ID `CAL-*`.
- Anomalía secundaria detectada de pasada: Sinaloa maíz dulce 2022–2024 con valores implícitos
  *altos* (496k–933k MXN/ha) — dirección opuesta; posible sub-reporte de superficie reciente.
