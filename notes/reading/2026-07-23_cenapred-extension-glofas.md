# Read-log 2026-07-23 — CENAPRED 2000–2023 y el panel fluvial GloFAS

Qué leer para respaldar las decisiones de esta sesión, y por qué cada lectura sostiene cuál. Claves de cita en [[REFERENCES]].

## Para `CAL-RF-04` (una sola metodología fluvial, no empalme)

**[Harrigan2020], ESSD 12(3):2043–2060 — §2 (producción del reanálisis) y §4 (evaluación contra aforos).** Es la referencia de GloFAS-ERA5 y lo que hay que leer para poder afirmar qué representa la descarga `dis24` y con qué sesgos: el artículo evalúa el reanálisis contra ~1,800 estaciones y documenta dónde el modelo hidrológico LISFLOOD sobre- o sub-estima caudal. La decisión de correr todo el panel con GloFAS descansa en que esa caracterización de error es **única y estacionaria** a lo largo de 2000–2023, algo que un empalme rompería.

**[WillnerISIMIP2024], documentación del dataset DerivedOutputData/Zimmer2023 — sección de metodología de las huellas.** Hay que leerla para saber exactamente qué produce CaMa-Flood/MATSIRO/GSWP3 y por qué su par `flddph`/`fldfrc` no es conmensurable celda a celda con la profundidad que devuelve `rf_glofas`: distinta rutina hidrodinámica, distinta malla nativa, distinto tratamiento de la llanura de inundación. Es el sustento conceptual del hallazgo empírico de que ISIMIP2a y GloFAS ordenan igual ($\rho_{\text{Spearman}} = 0.62$) pero difieren $\approx 2.44\times$ en nivel.

**[Huizinga2017], EUR 28552 EN — §3 (curvas por región/sector) y la discusión de incertidumbre.** Relevante aquí no por la curva en sí sino porque la comparación entre metodologías se hizo **en impacto modelado**, no en profundidad: la curva JRC es la que traduce profundidad a daño, y su no linealidad es la razón de que una diferencia moderada en profundidad se amplifique a $2.44\times$ en pérdida. Leer la sección de incertidumbre da la escala contra la cual juzgar si esa amplificación es tolerable.

**[Scussolini2016-ref?], NHESS 16:1049–1067 — §2 (construcción de las capas DB/PL/ML).** Para `OQ-CAL-16`, que sigue abierta y ahora aplica a un solo bloque fluvial: hay que saber qué mezcla de estándares de diseño, política y modelo entra en FLOPROS para México antes de elegir `none` o `flopros` en la verosimilitud, sobre todo sabiendo que la protección elimina la mayoría de los centroides con agua.

## Para `CAL-RF-03` (edición del ajuste Gumbel)

**[GumbelGloFAS-ref?], ETH Research Collection hdl:20.500.11850/726304 — README del dataset.** Leer para confirmar autoría y, sobre todo, **sobre qué versión y malla de GloFAS se ajustó**: el argumento de la decisión es que la edición 1979–2023 vive en la malla v4.0 de 0.05° y la 1979–2015 en la v3 de 0.1°, y que por eso sólo la primera es utilizable con la descarga congelada. Conviene además verificar el periodo de ajuste: un Gumbel ajustado a 1979–2023 incorpora los años que estamos calibrando, lo cual es correcto para estimar periodo de retorno climatológico pero conviene declararlo.

**[Dottori2016-ref?], Advances in Water Resources — sección de generación de los mapas rp10–rp500.** Es la otra mitad de la cadena: el periodo de retorno se convierte en profundidad interpolando estos mapas, así que su resolución (30 as) y su cobertura (sólo llanuras de inundación; ≈97% del bbox es NaN) explican la agregación 5×5 a los centroides y por qué las celdas sin cobertura cuentan como secas.

## Para `CAL-TARGET-06` (CENAPRED 2016–2023)

**Informes CENAPRED *Impacto socioeconómico de los principales desastres ocurridos en México*, extensos 2016–2023 — Tabla 1.1 y las tablas 2.x del capítulo hidrometeorológico de cada año.** Son la fuente primaria y los totales de control contra los que se concilió cada año. Hay que leerlas para entender el cambio estructural: desde 2016 el informe publica tablas estado×fenómeno y evento×estado sólo para ciclones y sismos, no el registro CENACOM completo — que es exactamente por qué la cola de eventos menores queda censurada y `INUND` se disuelve en `LLUV`.

**[BanxicoFIX2024], compilación de cuadros del Informe Anual — tipos de cambio representativos, promedio del periodo.** El FIX anual es el discriminante que separó catástrofe real de error de unidades en el segmento nuevo: la razón MDP/MDD debe reproducirlo, y lo hace con desvío 0.0%. Leer la nota metodológica del cuadro para saber qué promedio exactamente es (promedio del periodo, no cierre) antes de usarlo en el manuscrito.

**[Leys2013-ref?], JESP 49(4):764–766.** Sostiene el triaje del inspector (`CAL-GEN-14`) que se corrió sobre el segmento nuevo. Relectura pertinente porque esta sesión mostró su límite: el umbral "salto ≥1000× la mediana del grupo" está pensado para series casi estacionarias y marca como `error_probable` catástrofes legítimas en series de pérdida. El artículo justifica la z robusta, no el umbral; el umbral es `[eng]` y depende del dominio.

## Para `OQ-CAL-19` (deflactación)

**INEGI, *Índice Nacional de Precios al Consumidor* — nota metodológica y la serie anual.** Antes de fijar la ruta de obtención hay que decidir qué agregación anual se usa (promedio del año contra diciembre) y contra qué base; `CAL-TARGET-03` nombra el INPC pero no la ruta, y el relevo del Banco Mundial (`FP.CPI.TOTL`) es el mismo índice re-basado, no una cita equivalente (`CAL-GEN-01`).

## Related
[[CAL_MOC]] · [[DECISIONS]] · [[REFERENCES]] · [[OPEN_QUESTIONS]] · [[hazard-rf-glofas]] · [[target-rutaB-2000-2023]] · Home: [[_INDEX]]
#arm/cal #type/reading
