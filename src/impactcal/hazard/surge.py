"""Frozen TC storm-surge hazard on the shared centroids (DC-CAL-HAZ-1).

Computes `TCSurgeBathtub` (marejada, m; bathtub with the Xu 2010 wind-surge
relationship and inland decay, CAL-SURGE-01) from the frozen wind hazard
`haz_tc.h5` and the frozen SRTM15+ V2 DEM clip (CAL-SURGE-02) — the surge
events, dates and centroids are inherited from the wind hazard, so
CAL-HAZ-SHARED-01/02 hold by construction. Runs only against verified frozen
inputs (CAL-GEN-12). Before generating, the shoreline check of CAL-SURGE-02
runs: petals silently drops any coastal centroid whose DEM sample is nodata,
so a single nodata sample aborts with instructions to re-freeze the DEM
(`impactcal.hazard.freeze_inputs`). Writes `data/hazard/haz_surge.h5` +
`_procedencia.json` + run manifest. Idempotent: skips an artifact that
verifies unless `--forzar`.

CLI (run inside the CLIMADA env)::

    python -m impactcal.hazard.surge [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np

from impactcal.hazard.tc import _n_con_intensidad
from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance

_FUENTE_SURGE = (
    "TCSurgeBathtub (climada-petals) sobre haz_tc congelado + DEM SRTM15+ V2 recortado "
    "[Xu2010][Tozer2019]"
)

# Constantes de selección costera de petals (tc_surge_bathtub), replicadas para el chequeo previo.
_MAX_DIST_COSTA_M = 50 * 1000
_MAX_ELEVACION_M = 10
_MAX_LATITUD = 61

# Parámetros físicos: defaults de petals — decaimiento 0.2 m/km (Pielke & Pielke 1997, vía
# petals) y sin ajuste de nivel del mar (calibración histórica).
_DECAIMIENTO_M_KM = 0.2
_AUMENTO_NIVEL_MAR_M = 0.0


def coastal_dem_check(wind_haz, dem_path: Path) -> dict[str, int]:
    """CAL-SURGE-02: count DEM samples at the petals coastal mask; nodata there is fatal.

    Replicates the selection of `TCSurgeBathtub.from_tc_winds` (wind-affected, on land,
    within 50 km of the coast, |lat| <= 61) and samples the DEM exactly as petals does.
    """
    import climada.util.coordinates as u_coord

    cent = wind_haz.centroids
    dist_costa = cent.get_dist_coast(signed=True)
    msk = (wind_haz.intensity > 0).sum(axis=0).A1 > 0
    msk &= (dist_costa < 0) & (dist_costa >= -_MAX_DIST_COSTA_M)
    msk &= np.abs(cent.lat) <= _MAX_LATITUD
    h = u_coord.read_raster_sample(str(dem_path), cent.lat[msk], cent.lon[msk])
    return {
        "n_costeros_viento": int(msk.sum()),
        "n_nodata": int(np.isnan(h).sum()),
        "n_bajo_nivel_mar": int((h < 0).sum()),
        "n_elegibles_surge": int(((h >= 0) & (h <= _MAX_ELEVACION_M)).sum()),
    }


def load_frozen(path: Path, etiqueta: str) -> Path:
    """Verify a frozen input against its provenance before using it (CAL-GEN-12)."""
    if not verify_provenance(path):
        raise RuntimeError(f"{etiqueta} corrupto o sin procedencia: {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--forzar", action="store_true", help="regenera aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()
    salida = paths.data / "hazard" / "haz_surge.h5"
    if not args.forzar and verify_provenance(salida):
        print(f"intacto (usa --forzar para regenerar): {salida}")
        return 0

    haz_tc_path = load_frozen(paths.data / "hazard" / "haz_tc.h5", "Hazard viento congelado")
    dem_path = load_frozen(paths.data / Path(config["hazard"]["dem_path"]), "DEM congelado")

    from climada.hazard import TropCyclone

    tc = TropCyclone.from_hdf5(str(haz_tc_path))
    chequeo = coastal_dem_check(tc, dem_path)
    print(f"chequeo costero (CAL-SURGE-02): {chequeo}")
    if chequeo["n_nodata"]:
        raise RuntimeError(
            f"{chequeo['n_nodata']} centroides costeros muestrean nodata en el DEM: "
            "petals los descartaría en silencio. Re-congela el DEM con mayor buffer "
            "(hazard.dem_buffer_grados) vía impactcal.hazard.freeze_inputs."
        )

    from importlib.metadata import version

    from climada_petals.hazard import TCSurgeBathtub

    haz = TCSurgeBathtub.from_tc_winds(
        tc,
        str(dem_path),
        inland_decay_rate=_DECAIMIENTO_M_KM,
        add_sea_level_rise=_AUMENTO_NIVEL_MAR_M,
    )
    salida.parent.mkdir(parents=True, exist_ok=True)
    haz.write_hdf5(str(salida))
    write_provenance(
        salida,
        source=_FUENTE_SURGE,
        modelo="bañera Xu (2010) viento-marejada con decaimiento tierra adentro (petals)",
        unidades="m",
        inland_decay_rate_m_km=_DECAIMIENTO_M_KM,
        add_sea_level_rise_m=_AUMENTO_NIVEL_MAR_M,
        max_dist_costa_km=50,
        max_elevacion_m=_MAX_ELEVACION_M,
        chequeo_costero=chequeo,
        n_eventos=int(haz.intensity.shape[0]),
        n_eventos_con_intensidad=_n_con_intensidad(haz),
        n_centroides=int(haz.intensity.shape[1]),
        haz_tc_sha256=_sha256(haz_tc_path),
        dem_sha256=_sha256(dem_path),
        climada_version=version("climada"),
        climada_petals_version=version("climada-petals"),
    )
    print(f"hazard marejada: {salida} ({_n_con_intensidad(haz)} eventos con intensidad)")

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"haz_surge_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes="Hazard marejada congelado: determinista, sin RNG.",
    ).write(paths.manifests, paths.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
