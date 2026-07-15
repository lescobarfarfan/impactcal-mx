"""Per-state max-intensity footprints of the frozen TC hazards (CAL-XWALK-01 input).

For each event (SID) in the frozen `haz_tc.h5`/`haz_rain.h5` and each estado
(`cve_ent` of the frozen exposure, CAL-EXP-04), the maximum intensity over the
state's centroids — the table the hazard-side crosswalk v1 thresholds against
(wind > `v_thresh`, rain-cone threshold `OQ-CAL-02`). Output
`data/crosswalk/huellas_estatales.csv` (long; only rows with intensity > 0):
`sid, cve_ent, peril {viento|lluvia}, int_max` (m/s | mm), with provenance
chaining the hazard and exposure sha256. Deterministic; reads only verified
frozen inputs (CAL-GEN-12).

CLI (run inside the CLIMADA env)::

    python -m impactcal.hazard.footprints [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance

_FUENTE = (
    "Huellas estatales (max por evento×estado) de los hazards TC congelados "
    "(CAL-HAZ-SHARED-02) sobre la exposición LitPop (CAL-EXP-04) [eng]"
)


def state_max(intensity, event_names: list[str], cve_ent: np.ndarray) -> pd.DataFrame:
    """Max intensity per (event, estado) from a sparse events×centroids matrix.

    Returns a long DataFrame `sid, cve_ent, int_max` keeping only rows with
    intensity > 0.
    """
    filas = []
    for cve in sorted(set(cve_ent)):
        sub = intensity[:, np.flatnonzero(cve_ent == cve)]
        maximo = np.asarray(sub.max(axis=1).todense()).ravel()
        con = np.flatnonzero(maximo > 0)
        filas.append(
            pd.DataFrame(
                {"sid": np.asarray(event_names)[con], "cve_ent": cve, "int_max": maximo[con]}
            )
        )
    return pd.concat(filas, ignore_index=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--forzar", action="store_true", help="regenera aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()

    salida = paths.data / "crosswalk" / "huellas_estatales.csv"
    if not args.forzar and verify_provenance(salida):
        print(f"intacto (usa --forzar para regenerar): {salida}")
        return 0

    res_as = int(config["exposure"]["resolucion_arcsec"])
    exp_path = paths.data / "exposures" / f"litpop_mex_{res_as}as.hdf5"
    haz_paths = {
        "viento": paths.data / "hazard" / "haz_tc.h5",
        "lluvia": paths.data / "hazard" / "haz_rain.h5",
    }
    for p in (exp_path, *haz_paths.values()):
        if not verify_provenance(p):
            raise RuntimeError(f"Insumo congelado corrupto o sin procedencia: {p}")

    from climada.entity import Exposures
    from climada.hazard import Hazard

    exp = Exposures.from_hdf5(str(exp_path))
    cve_ent = exp.gdf["cve_ent"].to_numpy()

    tablas = []
    for peril, haz_path in haz_paths.items():
        haz = Hazard.from_hdf5(str(haz_path))
        tabla = state_max(haz.intensity, list(haz.event_name), cve_ent)
        tabla["peril"] = peril
        tablas.append(tabla)
    huellas = pd.concat(tablas, ignore_index=True)[["sid", "cve_ent", "peril", "int_max"]]
    huellas = huellas.sort_values(["peril", "sid", "cve_ent"]).reset_index(drop=True)

    salida.parent.mkdir(parents=True, exist_ok=True)
    huellas.to_csv(salida, index=False)
    write_provenance(
        salida,
        source=_FUENTE,
        insumos={p.name: _sha256(p) for p in (exp_path, *haz_paths.values())},
        unidades="viento m/s, lluvia mm acumulados por evento",
        n_filas=int(len(huellas)),
    )

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"huellas_estatales_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes="Huellas estatales de hazards TC congelados: determinista, sin RNG.",
    ).write(paths.manifests, paths.root)

    print(f"huellas: {salida} ({len(huellas)} filas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
