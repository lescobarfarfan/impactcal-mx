# Lectura 2026-07-14 — crosswalk v1 lado-hazard

Qué leer y por qué, por decisión de la sesión ([[crosswalk-v1-hazard-side]]). Claves en [[REFERENCES]]; las decisiones de la sesión son `[eng]` — estas lecturas las contextualizan, no las sustituyen.

Tuleya et al. (2007) [Tuleya2007]: la estructura radial de R-CLIPER y sus acumulados típicos en landfall — da escala física al **umbral del cono de 50 mm** (`CAL-XWALK-04`): un máximo estatal de 50 mm acumulados por evento es lluvia tropical clara pero lejos del percentil dañino, consistente con usar el cono como *pertenencia* al conjunto afectado y dejar el filtro de daño a $P_{thresh}$ (`CAL-IMPF-03`, `OQ-CAL-04`).

Eberenz et al. (2021) [Eberenz2021]: su manejo de asignación evento↔país y solapes tipo EM-DAT — el análogo del grano año×estado con pérdida anual agregada nunca particionada (`CAL-TARGET-02`, `CAL-XWALK-01`); releer al construir la máscara de inclusión (`DC-CAL-TARGET-4`) para tratar los flags v1 (`tormenta_sin_perdida`, `perdida_sin_tormenta_modelada`) igual que ellos tratan sus year-country excluidos.

Knapp et al. (2010) [Knapp2010] + [IBTrACSv04r01]: dónde terminan los best-tracks (disipación del centro) — explica la cola `perdida_sin_tormenta_modelada` (21 año-estado, mayormente interiores): los remanentes que CENAPRED reporta tierra adentro pueden quedar fuera del track IBTrACS y por tanto de toda huella modelada; es límite del insumo, no error del crosswalk.

## Related
[[CAL_MOC]] · [[crosswalk-v1-hazard-side]] · [[DECISIONS]] · [[REFERENCES]] · Home: [[_INDEX]]
#arm/cal #type/reading
