"""Timestep convergence test (OQ-CAL-01, CAL-WIND-02; protocol: master doc §3.4).

For 3-4 major storms, computes `TropCyclone` wind fields at timestep
∈ {0.25, 0.5, 1, 3} h on regular centroid grids at two resolutions, and
compares against the finest timestep: (a) the per-cell max-intensity swath,
(b) the aggregate loss under a **fixed** Emanuel reference function — the
convergence criterion is agreement across timesteps, never the magnitude of
the result. The timestep × centroid-resolution interaction (the observed
finer-timestep → lower-losses anomaly) falls out of the resolution contrast.

Notes. The definitive calibration grid (LitPop centroids, `CAL-HAZ-SHARED-01`)
does not exist yet; the test brackets it with regular grids and must be
re-confirmed on the final grid before hazards freeze. State-level aggregation
per the protocol uses Natural Earth admin-1 polygons as a **test-only proxy**
of the Marco Geoestadístico (`DC-CONV-5`) when available; otherwise national.

CLI (run inside the CLIMADA env)::

    python -m impactcal.hazard.timestep_test [--config RUTA]
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths


def swath_metrics(v_ref: np.ndarray, v_alt: np.ndarray, v_thresh: float) -> dict[str, float]:
    """Per-cell max-intensity swath comparison of an alternative vs the reference.

    Metrics restricted to cells touched by either swath; all in m/s except the
    cell counts above `v_thresh` (damaging-wind footprint area).
    """
    diff = v_alt - v_ref
    mask = (v_ref > 0) | (v_alt > 0)
    if not mask.any():
        return {
            "rmse_ms": 0.0,
            "bias_ms": 0.0,
            "max_abs_ms": 0.0,
            "max_int_ref_ms": 0.0,
            "max_int_alt_ms": 0.0,
            "celdas_thresh_ref": 0,
            "celdas_thresh_alt": 0,
        }
    return {
        "rmse_ms": float(np.sqrt(np.mean(diff[mask] ** 2))),
        "bias_ms": float(np.mean(diff[mask])),
        "max_abs_ms": float(np.max(np.abs(diff[mask]))),
        "max_int_ref_ms": float(v_ref.max()),
        "max_int_alt_ms": float(v_alt.max()),
        "celdas_thresh_ref": int((v_ref > v_thresh).sum()),
        "celdas_thresh_alt": int((v_alt > v_thresh).sum()),
    }


def _admin1_labels(lat: np.ndarray, lon: np.ndarray) -> pd.Series | None:
    """State label per centroid via Natural Earth admin-1 (test-only proxy of
    the Marco Geoestadístico); None if the geometries are unavailable."""
    try:
        import geopandas as gpd
        from climada.util.coordinates import get_admin1_geometries

        estados = get_admin1_geometries(["MEX"])
        puntos = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(lon, lat), crs=estados.crs or "EPSG:4326"
        )
        join = gpd.sjoin(puntos, estados, how="left", predicate="within")
        col = "admin1_name" if "admin1_name" in join.columns else "name"
        return join[col].reindex(range(len(puntos)))
    except Exception:
        return None


def _exposure_and_centroids(cfg: dict[str, Any], res_as: int):
    """Exposure + matching hazard centroids for one resolution.

    `exposicion: litpop` puts the hazard on the LitPop centroids (the
    CAL-HAZ-SHARED-01 pattern) with real asset values; `uniforme` uses a
    regular bbox grid with value 1 per cell (loss = damage-weighted cell
    count). LitPop falls back to the uniform grid if it cannot be built.
    """
    from climada.entity import Exposures
    from climada.hazard import Centroids

    if cfg.get("exposicion", "litpop") == "litpop":
        try:
            from climada.entity import LitPop

            exp = LitPop.from_countries(["MEX"], res_arcsec=res_as)
            exp.gdf["impf_TC"] = 1
            cent = Centroids.from_lat_lon(exp.latitude, exp.longitude)
            return exp, cent, "litpop"
        except Exception as err:  # documented fallback, never silent
            print(f"AVISO: LitPop no construible ({err}); malla uniforme de respaldo.")
    bbox = cfg["bbox"]
    cent = Centroids.from_pnt_bounds(
        (bbox["lon_min"], bbox["lat_min"], bbox["lon_max"], bbox["lat_max"]), res_as / 3600
    )
    exp = Exposures(
        pd.DataFrame(
            {
                "latitude": cent.lat,
                "longitude": cent.lon,
                "value": np.ones(cent.size),
                "impf_TC": np.ones(cent.size, dtype=int),
            }
        )
    )
    return exp, cent, "uniforme"


def run_test(config: dict[str, Any]) -> pd.DataFrame:
    """Run the full convergence matrix; returns one row per
    (evento, resolución, timestep) with swath and loss metrics vs the finest
    timestep on the same grid."""
    from climada.engine import ImpactCalc
    from climada.entity import ImpactFuncSet, ImpfTropCyclone
    from climada.hazard import TCTracks, TropCyclone

    cfg = config["timestep_test"]
    timesteps = sorted(float(t) for t in cfg["timesteps_horas"])
    ts_ref = timesteps[0]
    v_thresh = float(config["impacto"]["v_thresh"])

    impf = ImpfTropCyclone.from_emanuel_usa(
        impf_id=1, v_thresh=v_thresh, v_half=float(cfg["ref_v_half"]), scale=1.0
    )
    impfset = ImpactFuncSet([impf])

    filas = []
    for res_as in cfg["resoluciones_arcsec"]:
        exp, cent, etiqueta_exp = _exposure_and_centroids(cfg, res_as)
        estados = _admin1_labels(cent.lat, cent.lon)

        for ev in cfg["eventos"]:
            base = TCTracks.from_ibtracs_netcdf(storm_id=ev["sid"])
            swaths: dict[float, np.ndarray] = {}
            perdidas: dict[float, float] = {}
            perdidas_estado: dict[float, pd.Series] = {}
            for ts in timesteps:
                tracks = copy.deepcopy(base)
                tracks.equal_timestep(ts)
                tc = TropCyclone.from_tracks(tracks, centroids=cent)
                swaths[ts] = np.asarray(tc.intensity.max(axis=0).todense()).ravel()
                imp = ImpactCalc(exp, impfset, tc).impact(save_mat=estados is not None)
                perdidas[ts] = float(imp.at_event.sum())
                if estados is not None:
                    por_celda = np.asarray(imp.imp_mat.sum(axis=0)).ravel()
                    perdidas_estado[ts] = pd.Series(por_celda).groupby(estados.values).sum()

            for ts in timesteps:
                fila = {
                    "evento": ev["nombre"],
                    "sid": ev["sid"],
                    "resolucion_arcsec": res_as,
                    "exposicion": etiqueta_exp,
                    "timestep_h": ts,
                    "timestep_ref_h": ts_ref,
                    **swath_metrics(swaths[ts_ref], swaths[ts], v_thresh),
                    "perdida_rel": perdidas[ts] / perdidas[ts_ref] if perdidas[ts_ref] else 1.0,
                }
                if estados is not None:
                    ref, alt = perdidas_estado[ts_ref], perdidas_estado[ts]
                    top = ref.sort_values(ascending=False).head(5).index
                    ratios = (alt.reindex(top) / ref.reindex(top)).round(4)
                    fila["perdida_rel_top5_estados"] = ";".join(
                        f"{e}:{r}" for e, r in ratios.items()
                    )
                filas.append(fila)
    return pd.DataFrame(filas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()

    metricas = run_test(config)

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = paths.results / "timestep_test"
    out_dir.mkdir(parents=True, exist_ok=True)
    salida = out_dir / f"metricas_convergencia_{ts}.csv"
    metricas.to_csv(salida, index=False)

    RunManifest(
        run_id=f"timestep_test_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes="Test de convergencia de timestep (OQ-CAL-01): determinista, sin RNG.",
    ).write(paths.manifests, paths.root)

    print(f"métricas: {salida}")
    with pd.option_context("display.width", 200):
        cols = [
            "evento",
            "resolucion_arcsec",
            "timestep_h",
            "rmse_ms",
            "bias_ms",
            "celdas_thresh_alt",
            "perdida_rel",
        ]
        print(metricas[cols].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
