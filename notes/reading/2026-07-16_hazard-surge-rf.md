# 2026-07-16 — Lecturas: hazards surge + RF congelados, insumos GloFAS

Qué leer y por qué, por decisión de la sesión (claves en [[REFERENCES]]).

**[Xu2010]** — Xu, L. (2010), *A Simple Coastline Storm Surge Model Based on Pre-run SLOSH Outputs* (AMS 29th Conf. Hurricanes; venue exacto = `OQ-CAL-08`). Leer la fig. 2 y la derivación de la relación lineal viento–marejada que petals implementa tal cual: $S = 0.1023\,\max(V - 26.8224,\,0) + 1.8288$ (m, con $V$ en m/s). Respadla la entrega de `CAL-SURGE-01` (`haz_surge.h5`): conviene entender que la pendiente/ordenada vienen de ajustar salidas SLOSH pre-corridas en costa de EE. UU. — un sesgo consistente para México lo absorbe $\kappa_s^{surge}$ (`CAL-IMPF-02`).

**[PetalsDocs]** — documentación de `TCSurgeBathtub` (petals v6). Leer la sección del modelo bañera: selección costera ($\le 50$ km de costa, $|lat| \le 61°$, $0 \le h \le 10$ m) y decaimiento tierra adentro 0.2 m/km (Pielke & Pielke 1997 §5.2.1, citado vía petals). Respalda los parámetros fijados en defaults en la entrega de `CAL-SURGE-01` `[eng]` y explica el mecanismo del descarte silencioso que motivó el supersede de `CAL-SURGE-02`: una muestra DEM `NaN` falla ambas desigualdades y el centroide sale de la máscara sin aviso.

**[Tozer2019]** — SRTM15+ V2. Leer la descripción del producto (§2–3): es topo-batimetría global **continua, sin huecos**. Por qué: la copia global pineada (3.4 GB) sí tiene 16,325 celdas nodata en la ventana México (lagunas costeras, Isla Clarión) — es decir, es un derivado pre-procesado, no el producto puro; el relleno por vecinos del congelado (`CAL-SURGE-02` superseded) es la corrección documentada, y la nota en [[REFERENCES]] lo deja asentado antes del manuscrito.

**[WillnerISIMIP2024]** — dataset ISIMIP DerivedOutputData/Zimmer2023 (doi:10.48364/ISIMIP.303619). Leer la ficha del repositorio: definición del **máximo anual** de profundidad/fracción (consistente con la unidad año×estado, `CAL-TARGET-02`) y las variantes de protección `none`/`flopros`. Respalda la entrega de `CAL-RF-02` (`haz_rf_{none,flopros}.h5`, 2000–2010).

**[Harrigan2020]** — GloFAS-ERA5 (ESSD 12, 2043–2060). Leer §2 (cadena de producción del reanálisis) y el versionado: nuestra descarga cruda es **v4.0 consolidated**; los ajustes Gumbel congelados se calcularon sobre 1979–2015 (era v3). Respalda `CAL-RF-03` y motiva la sub-decisión (c) de `OQ-CAL-17`: consistencia versión-del-fit ↔ versión-de-descarga.

**[Dottori2016-ref?]** — marco de los mapas JRC de peligro de inundación (rp10–rp500; cita exacta = `OQ-CAL-08`). Leer la metodología de mapeo periodo-de-retorno → profundidad: es exactamente la interpolación que `rf_glofas` hará en el paso de cómputo de `OQ-CAL-17`, así que el supuesto hidráulico del segmento 2011–2015 vive en este trabajo.

**[Scussolini2016-ref?]** — FLOPROS (NHESS 16, 1049–1067; verificar autores = `OQ-CAL-08`). Leer §3 (capas design/policy/model del estándar de protección) con ojo en la cobertura para México — es grueso a nivel subnacional, argumento central para decidir `OQ-CAL-16` con datos y no a priori.

**[GumbelGloFAS-ref?]** — ficha del dataset ETH (hdl:20.500.11850/641667; autores/DOI = `OQ-CAL-08`). Leer la descripción: parámetros $\mu$ (`loc`) y $\beta$ (`scale`) de Gumbel por celda a 0.1°, ventana 1979–2015, y comparar con la edición 1979–2023 (hdl:20.500.11850/726304) antes del cómputo de `OQ-CAL-17`.

## Related
[[CAL_MOC]] · [[REFERENCES]] · [[DECISIONS]] · [[hazard-surge-generation]] · [[hazard-rf-isimip]] · Home: [[_INDEX]]
#arm/cal #type/reading
