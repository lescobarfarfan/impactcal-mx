"""Frozen TC wind and cyclonic-rain hazards on the shared centroids (DC-CAL-HAZ-1).

Computes `TropCyclone` (viento, m/s, CAL-WIND-01) and `TCRain` (lluvia, mm;
R-CLIPER per CAL-RAIN-01, model choice pending OQ-CAL-03) for the near-Mexico
storm universe of the frozen IBTrACS index — EP+NA, seasons
`periodo.anio_inicial`..`hazard.temporada_max`, any track point inside the
crosswalk bbox — on the centroids of the frozen LitPop exposure
(CAL-HAZ-SHARED-01), tracks interpolated at the frozen 0.5 h timestep
(CAL-WIND-02). Runs only against verified frozen inputs (CAL-GEN-12): the
CLIMADA IBTrACS cache is hash-checked against `data/ibtracs/crudos/` and
restored from it on divergence (CAL-WIND-03). Writes
`data/hazard/haz_{tc,rain}.h5` + `_procedencia.json` + run manifest.
Idempotent: an artifact that verifies is skipped — delete one `.h5` to
regenerate only that peril, or `--forzar` for both.

CLI (run inside the CLIMADA env)::

    python -m impactcal.hazard.tc [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

import pandas as pd

from impactcal.hazard.ibtracs import NC_CACHE, load_storm_index
from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance

_FUENTE_TC = (
    "TropCyclone (H08) sobre centroides LitPop congelados, IBTrACS v04r01 EP+NA "
    "[Knapp2010][IBTrACSv04r01][Eberenz2021]"
)

_FUENTE_RAIN = (
    "TCRain R-CLIPER (climada-petals) sobre centroides LitPop congelados, IBTrACS v04r01 EP+NA "
    "[Tuleya2007][Knapp2010][IBTrACSv04r01]"
)


def ensure_ibtracs_cache(frozen_nc: Path, cache_nc: Path) -> str:
    """CAL-WIND-03: the CLIMADA cache must hash-match the frozen copy.

    Verifies the frozen copy against its provenance, then restores the cache
    from it when the cache is missing or diverges. Returns the frozen sha256.
    """
    if not verify_provenance(frozen_nc):
        raise RuntimeError(f"Copia congelada corrupta o sin procedencia: {frozen_nc}")
    prov = frozen_nc.with_name(frozen_nc.name + "._procedencia.json")
    sha = json.loads(prov.read_text(encoding="utf-8"))["sha256"]
    if not cache_nc.exists() or _sha256(cache_nc) != sha:
        cache_nc.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(frozen_nc, cache_nc)
        print(f"caché IBTrACS restaurada desde la copia congelada: {cache_nc}")
    return sha


def select_storms(index: pd.DataFrame, temporada_max: int) -> list[str]:
    """SIDs of the hazard universe: near-Mexico storms up to the last complete season."""
    sel = index[index["toca_mexico"] & (index["season"] <= temporada_max)]
    return sel["sid"].tolist()


def load_shared_centroids(exp_path: Path):
    """Hazard centroids = coordinates of the frozen exposure (CAL-HAZ-SHARED-01)."""
    from climada.entity import Exposures
    from climada.hazard import Centroids

    if not verify_provenance(exp_path):
        raise RuntimeError(f"Exposición congelada corrupta o sin procedencia: {exp_path}")
    exp = Exposures.from_hdf5(str(exp_path))
    return Centroids.from_lat_lon(exp.latitude, exp.longitude)


def _n_con_intensidad(haz) -> int:
    """Events with any nonzero cell — storms that actually touch the grid."""
    return int((haz.intensity.getnnz(axis=1) > 0).sum())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--forzar", action="store_true", help="regenera aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()
    cfg = config["hazard"]

    out_dir = paths.data / "hazard"
    salidas = {"viento": out_dir / "haz_tc.h5", "lluvia": out_dir / "haz_rain.h5"}
    pendientes = {
        peril: ruta for peril, ruta in salidas.items() if args.forzar or not verify_provenance(ruta)
    }
    if not pendientes:
        print(f"intactos (usa --forzar para regenerar): {', '.join(map(str, salidas.values()))}")
        return 0

    ibtracs_dir = paths.data / "ibtracs" / "crudos"
    sha_nc = ensure_ibtracs_cache(
        ibtracs_dir / NC_CACHE, Path(config["fuentes_externas"]["ibtracs_nc"]).expanduser()
    )

    res_as = int(config["exposure"]["resolucion_arcsec"])
    exp_path = paths.data / "exposures" / f"litpop_mex_{res_as}as.hdf5"
    cent = load_shared_centroids(exp_path)

    anio_inicial = int(config["periodo"]["anio_inicial"])
    temporada_max = int(cfg["temporada_max"])
    index = load_storm_index(
        ibtracs_dir, season_min=anio_inicial, bbox=config["crosswalk"]["bbox_mexico"]
    )
    sids = select_storms(index, temporada_max)
    print(f"universo: {len(sids)} tormentas cerca de México, {anio_inicial}-{temporada_max}")

    from climada.hazard import TCTracks

    tracks = TCTracks.from_ibtracs_netcdf(
        provider=cfg["ibtracs_provider"],
        storm_id=sids,
        estimate_missing=bool(cfg["estimate_missing"]),
    )
    sin_track = sorted(set(sids) - {t.sid for t in tracks.data})
    if sin_track:
        print(f"AVISO: {len(sin_track)} SIDs sin track utilizable: {';'.join(sin_track)}")
    tracks.equal_timestep(float(cfg["timestep_horas"]))

    from importlib.metadata import version

    comunes = {
        "universo": (
            f"IBTrACS v04r01 EP+NA, temporadas {anio_inicial}-{temporada_max}, "
            "algún punto de trayectoria en crosswalk.bbox_mexico"
        ),
        "bbox": config["crosswalk"]["bbox_mexico"],
        "provider": cfg["ibtracs_provider"],
        "estimate_missing": bool(cfg["estimate_missing"]),
        "timestep_horas": float(cfg["timestep_horas"]),
        "n_tormentas": tracks.size,
        "sids_sin_track": ";".join(sin_track) or "ninguno",
        "centroides_archivo": exp_path.name,
        "centroides_sha256": _sha256(exp_path),
        "n_centroides": int(cent.size),
        "ibtracs_nc_sha256": sha_nc,
        "climada_version": version("climada"),
    }

    out_dir.mkdir(parents=True, exist_ok=True)

    if "viento" in pendientes:
        from climada.hazard import TropCyclone

        haz = TropCyclone.from_tracks(tracks, centroids=cent)
        haz.write_hdf5(str(pendientes["viento"]))
        write_provenance(
            pendientes["viento"],
            source=_FUENTE_TC,
            modelo="H08 (Holland 2008), default CLIMADA",
            unidades="m/s",
            intensity_thres_ms=17.5,
            n_eventos_con_intensidad=_n_con_intensidad(haz),
            **comunes,
        )
        print(f"hazard viento: {pendientes['viento']}")

    if "lluvia" in pendientes:
        from climada_petals.hazard import TCRain

        haz = TCRain.from_tracks(tracks, centroids=cent, model="R-CLIPER")
        haz.write_hdf5(str(pendientes["lluvia"]))
        write_provenance(
            pendientes["lluvia"],
            source=_FUENTE_RAIN,
            modelo="R-CLIPER (default petals; R-CLIPER vs TCR = OQ-CAL-03)",
            unidades="mm acumulados por evento",
            intensity_thres_mm=0.1,
            n_eventos_con_intensidad=_n_con_intensidad(haz),
            climada_petals_version=version("climada-petals"),
            **comunes,
        )
        print(f"hazard lluvia: {pendientes['lluvia']}")

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"haz_tc_rain_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes=f"Hazards TC congelados ({', '.join(pendientes)}): determinista, sin RNG.",
    ).write(paths.manifests, paths.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
