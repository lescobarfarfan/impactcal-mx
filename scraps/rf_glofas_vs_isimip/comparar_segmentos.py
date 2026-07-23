"""OQ-CAL-17(b): ¿pueden ISIMIP2a y GloFAS compartir una misma verosimilitud?

Compara los dos segmentos fluviales en los años de traslape (ambos cubren
2000-2010) sobre los MISMOS centroides y la MISMA exposición, en tres planos:

1. huella cruda        — centroides mojados, profundidad, fracción inundada
2. huella por estado   — centroides mojados por estado×año
3. **impacto modelado** — la única capa que ve la verosimilitud: pérdida por
   estado×año con la curva JRC (CAL-IMPF-02) sobre LitPop congelado

Un splice sólo es defendible si (3) concuerda; si no, el panel fluvial debe
correrse con una sola metodología (GloFAS 2000-2023).

Uso (dentro del env CLIMADA)::

    IMPACTCAL_DATA_ROOT=<repo>/data python scraps/rf_glofas_vs_isimip/comparar_segmentos.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from impactcal.infra.paths import ProjectPaths
from impactcal.target.crosswalk import ENTIDAD_A_CVE  # noqa: F401  (documenta la convención)

SALIDA = Path(__file__).parent


def cargar():
    from climada.entity import Exposures
    from climada.hazard import Hazard

    paths = ProjectPaths()
    hz = paths.data / "hazard"
    exp = Exposures.from_hdf5(str(paths.data / "exposures" / "litpop_mex_150as.hdf5"))
    isimip = Hazard.from_hdf5(str(hz / "haz_rf_none.h5"))
    glofas = Hazard.from_hdf5(str(hz / "haz_rf_glofas_none.h5"))
    return exp, isimip, glofas


def anios_de(haz) -> list[int]:
    return [int(n) for n in haz.event_name]


def resumen_huella(haz, anios_ok: list[int], etiqueta: str) -> pd.DataFrame:
    filas = []
    for k, anio in enumerate(anios_de(haz)):
        if anio not in anios_ok:
            continue
        inten = haz.intensity[k]
        frac = haz.fraction[k]
        filas.append(
            {
                "anio": anio,
                "metodo": etiqueta,
                "centroides_mojados": int(inten.nnz),
                "prof_media_m": float(inten.data.mean()) if inten.nnz else 0.0,
                "prof_max_m": float(inten.data.max()) if inten.nnz else 0.0,
                "frac_media": float(frac.data.mean()) if frac.nnz else 0.0,
                "area_equivalente": float(frac.sum()),
            }
        )
    return pd.DataFrame(filas)


def impacto_por_estado(exp, haz, anios_ok: list[int], etiqueta: str) -> pd.DataFrame:
    """Pérdida modelada por estado×año con la curva JRC (CAL-IMPF-02)."""
    from climada.engine import ImpactCalc
    from climada.entity import ImpactFuncSet
    from climada_petals.entity.impact_funcs.river_flood import ImpfRiverFlood

    impf = ImpfRiverFlood.from_jrc_region_sector("NorthAmerica", "residential")
    impf.haz_type, impf.id = "RF", 1
    impf_set = ImpactFuncSet([impf])

    exp = exp.copy()
    exp.gdf["impf_RF"] = 1
    cve = exp.gdf["region_id"].astype(int).astype(str).str.zfill(2).values

    imp = ImpactCalc(exp, impf_set, haz).impact(save_mat=True)
    mat = imp.imp_mat.tocsr()
    filas = []
    for k, anio in enumerate(anios_de(haz)):
        if anio not in anios_ok:
            continue
        fila = np.asarray(mat[k].todense()).ravel()
        for c in np.unique(cve):
            filas.append(
                {
                    "anio": anio,
                    "cve_ent": c,
                    "metodo": etiqueta,
                    "perdida": float(fila[cve == c].sum()),
                }
            )
    return pd.DataFrame(filas)


def main() -> int:
    exp, isimip, glofas = cargar()
    traslape = sorted(set(anios_de(isimip)) & set(anios_de(glofas)))
    print(f"años de traslape: {traslape}")
    if not traslape:
        print("sin traslape: no se puede evaluar la consistencia todavía")
        return 1

    huellas = pd.concat(
        [resumen_huella(isimip, traslape, "isimip2a"), resumen_huella(glofas, traslape, "glofas")]
    )
    huellas.to_csv(SALIDA / "huella_por_anio.csv", index=False)
    print("\n=== huella cruda por año ===")
    print(huellas.pivot(index="anio", columns="metodo", values="centroides_mojados").to_string())

    imp = pd.concat(
        [
            impacto_por_estado(exp, isimip, traslape, "isimip2a"),
            impacto_por_estado(exp, glofas, traslape, "glofas"),
        ]
    )
    imp.to_csv(SALIDA / "impacto_estado_anio.csv", index=False)

    ancho = imp.pivot_table(
        index=["anio", "cve_ent"], columns="metodo", values="perdida"
    ).reset_index()
    ancho = ancho[(ancho["isimip2a"] > 0) | (ancho["glofas"] > 0)]
    print(f"\n=== impacto modelado: {len(ancho)} pares estado×año con daño en algún método ===")
    tot_i, tot_g = ancho["isimip2a"].sum(), ancho["glofas"].sum()
    print(f"total isimip2a: {tot_i:.3e}   total glofas: {tot_g:.3e}")
    print(f"razón glofas/isimip2a: {ancho['glofas'].sum()/max(ancho['isimip2a'].sum(),1):.3f}")
    print(f"correlación Pearson : {ancho['isimip2a'].corr(ancho['glofas']):.3f}")
    print(f"correlación Spearman: {ancho['isimip2a'].corr(ancho['glofas'], method='spearman'):.3f}")
    ambos = ancho[(ancho["isimip2a"] > 0) & (ancho["glofas"] > 0)]
    print(f"pares con daño en AMBOS: {len(ambos)} ({100*len(ambos)/len(ancho):.1f}%)")
    if len(ambos):
        lr = np.log10(ambos["glofas"] / ambos["isimip2a"])
        print(
            f"log10(glofas/isimip2a): mediana {lr.median():.2f}  "
            f"p10 {lr.quantile(.1):.2f}  p90 {lr.quantile(.9):.2f}"
        )
    ancho.to_csv(SALIDA / "impacto_comparado_ancho.csv", index=False)
    print(f"\nsalidas -> {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
