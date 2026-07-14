"""LitPop MEX exposure, ruta B (CAL-EXP-01/03; contract DC-CAL-EXP-1).

Builds `LitPop.from_countries(['MEX'])` at the configured resolution, assigns
`cve_ent`/`region_id` = clave INEGI (2-digit) via spatial join with the frozen
Marco Geoestadístico `00ent` layer (nearest-state fallback for coastal cells),
sets `impf_TC = impf_TCSurgeBathtub = impf_TR = impf_RF` = clave, and persists
`data/exposures/litpop_mex_<res>as.hdf5` with provenance + run manifest.
Values in USD of the LitPop reference year; conversion documented downstream
(DC-CAL-EXP-1). Ruta A (CNSF sums insured, CAL-EXP-02) is gated on OQ-CAL-11.

CLI (run inside the CLIMADA env)::

    python -m impactcal.exposure.litpop [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Any

import numpy as np

from impactcal.infra.config import load_config
from impactcal.infra.freeze import freeze_copy
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import verify_provenance, write_provenance

MARCO_PARTES = ("00ent.shp", "00ent.dbf", "00ent.shx", "00ent.prj", "00ent.cpg")

IMPF_COLS = ("impf_TC", "impf_TCSurgeBathtub", "impf_TR", "impf_RF")

_FUENTE_MARCO = (
    "INEGI Marco Geoestadístico, capa nacional de entidades federativas (00ent) "
    "[versión por confirmar — OQ]"
)

_FUENTE_LITPOP = (
    "LitPop MEX (climada LitPop.from_countries): luces nocturnas x población " "[Eberenz2020LitPop]"
)


def freeze_marco(src_dir: Path, dest_dir: Path, *, force: bool = False) -> list[Path]:
    """Freeze the 00ent shapefile set with provenance."""
    return [
        freeze_copy(src_dir / nombre, dest_dir, source=_FUENTE_MARCO, force=force)
        for nombre in MARCO_PARTES
    ]


def assign_states(lat: np.ndarray, lon: np.ndarray, estados: Any) -> np.ndarray:
    """Clave INEGI (2-digit str) per point: within-join, nearest fallback.

    Boundary points matching two states keep the first match; points outside
    every polygon (coastal LitPop cells) take the nearest state.
    """
    import geopandas as gpd

    estados = estados.to_crs("EPSG:4326")[["CVEGEO", "geometry"]]
    puntos = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs="EPSG:4326")
    join = gpd.sjoin(puntos, estados, how="left", predicate="within")
    join = join[~join.index.duplicated(keep="first")]
    cve = join["CVEGEO"].reindex(range(len(puntos)))
    faltan = cve.isna().to_numpy()
    if faltan.any():
        # Nearest needs a projected CRS; EPSG:6372 (México ITRF2008/LCC) is the layer's native.
        cerca = gpd.sjoin_nearest(
            puntos[faltan].to_crs("EPSG:6372"), estados.to_crs("EPSG:6372"), how="left"
        )
        cerca = cerca[~cerca.index.duplicated(keep="first")]
        cve.loc[faltan] = cerca["CVEGEO"]
    return cve.to_numpy()


def build_exposure(config: dict[str, Any], marco_dir: Path):
    """LitPop MEX with state keys and per-peril impf assignment (CAL-EXP-03)."""
    import geopandas as gpd
    from climada.entity import LitPop

    cfg = config["exposure"]
    exp = LitPop.from_countries(
        ["MEX"],
        res_arcsec=int(cfg["resolucion_arcsec"]),
        reference_year=int(cfg["anio_referencia"]),
        fin_mode=cfg["fin_mode"],
    )
    estados = gpd.read_file(marco_dir / "00ent.shp")
    cve = assign_states(np.asarray(exp.latitude), np.asarray(exp.longitude), estados)
    clave = cve.astype(int)
    exp.gdf["cve_ent"] = cve
    exp.gdf["region_id"] = clave
    for col in IMPF_COLS:
        exp.gdf[col] = clave
    return exp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--forzar", action="store_true", help="regenera aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()
    cfg = config["exposure"]

    marco_dir = paths.data / "marco_geoestadistico"
    for p in freeze_marco(
        Path(config["fuentes_externas"]["marco_geoestadistico"]).expanduser(),
        marco_dir,
        force=args.forzar,
    ):
        print(f"congelado: {p}")

    salida = paths.data / "exposures" / f"litpop_mex_{cfg['resolucion_arcsec']}as.hdf5"
    if not args.forzar and verify_provenance(salida):
        print(f"intacto (usa --forzar para regenerar): {salida}")
        return 0

    exp = build_exposure(config, marco_dir)
    salida.parent.mkdir(parents=True, exist_ok=True)
    exp.write_hdf5(str(salida))

    from importlib.metadata import version

    write_provenance(
        salida,
        source=_FUENTE_LITPOP,
        resolucion_arcsec=int(cfg["resolucion_arcsec"]),
        anio_referencia=int(cfg["anio_referencia"]),
        fin_mode=cfg["fin_mode"],
        unidades="USD del año de referencia (conversión documentada aguas abajo)",
        nota_gpw="GPW v4.11: año 2020, el más cercano disponible al de referencia",
        n_centroides=int(len(exp.gdf)),
        valor_total_usd=float(exp.gdf["value"].sum()),
        climada_version=version("climada"),
    )

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"litpop_mex_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes="Exposición LitPop MEX (ruta B, CAL-EXP-01/03): determinista, sin RNG.",
    ).write(paths.manifests, paths.root)

    print(f"exposición: {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
