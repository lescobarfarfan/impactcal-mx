"""Frozen river-flood footprints on the shared centroids (DC-CAL-HAZ-1, CAL-RF-02).

Builds `RiverFlood` (inundación fluvial, m + fracción inundada) from the
frozen ISIMIP2a observed-forcing footprints (CaMa-Flood/MATSIRO/GSWP3,
annual maxima — consistent with the año×estado unit, CAL-TARGET-02) on the
centroids of the frozen LitPop exposure (CAL-HAZ-SHARED-01), panel years
`periodo.anio_inicial`..2010 (the ISIMIP2a segment; 2011-2015 = GloFAS,
OQ-CAL-17). Both protection variants are frozen — `none` and `flopros` —
because the likelihood choice is open (OQ-CAL-16). NaN cells at centroids
(outside the CaMa-Flood land mask, i.e. no fluvial model there) are zeroed
and counted in the provenance. Writes `data/hazard/haz_rf_{none,flopros}.h5`
+ `_procedencia.json` + run manifest. Idempotent: an artifact that verifies
is skipped — delete one `.h5` to regenerate only that variant, or `--forzar`
for both.

CLI (run inside the CLIMADA env)::

    python -m impactcal.hazard.rf [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np

from impactcal.hazard.tc import load_shared_centroids
from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance

PROTECCIONES = ("none", "flopros")

_FUENTE_RF = (
    "RiverFlood (climada-petals) sobre centroides LitPop congelados, huellas ISIMIP2a "
    "CaMa-Flood/MATSIRO/GSWP3 (DerivedOutputData/Zimmer2023) [WillnerISIMIP2024][Sauer2021-ref?]"
)


def isimip_pair(isimip_dir: Path, proteccion: str) -> tuple[Path, Path]:
    """The frozen (depth, fraction) ISIMIP2a NetCDF pair for one protection level."""
    pares = []
    for variable in ("flddph", "fldfrc"):
        hits = sorted(isimip_dir.glob(f"cama-flood_*_{variable}_{proteccion}_*.nc4"))
        if len(hits) != 1:
            raise RuntimeError(
                f"se esperaba exactamente 1 archivo {variable}/{proteccion} en {isimip_dir}, "
                f"hay {len(hits)}"
            )
        pares.append(hits[0])
    return pares[0], pares[1]


def select_years(anios_nc: list[int], anio_inicial: int) -> list[int]:
    """Panel years served by the ISIMIP2a segment: from `anio_inicial` to the end of the nc."""
    anios = [a for a in anios_nc if a >= anio_inicial]
    if not anios:
        raise RuntimeError(f"el nc ISIMIP2a no cubre ningún año >= {anio_inicial}")
    return anios


def sanitize_nan(haz) -> int:
    """Zero NaN cells (centroids outside the CaMa-Flood land mask) in intensity and fraction."""
    n = 0
    for mat in (haz.intensity, haz.fraction):
        nan_msk = np.isnan(mat.data)
        n = max(n, int(nan_msk.sum()))
        mat.data[nan_msk] = 0.0
        mat.eliminate_zeros()
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--forzar", action="store_true", help="regenera aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()
    out_dir = paths.data / "hazard"
    salidas = {p: out_dir / f"haz_rf_{p}.h5" for p in PROTECCIONES}
    pendientes = {
        prot: ruta for prot, ruta in salidas.items() if args.forzar or not verify_provenance(ruta)
    }
    if not pendientes:
        print(f"intactos (usa --forzar para regenerar): {', '.join(map(str, salidas.values()))}")
        return 0

    res_as = int(config["exposure"]["resolucion_arcsec"])
    exp_path = paths.data / "exposures" / f"litpop_mex_{res_as}as.hdf5"
    cent = load_shared_centroids(exp_path)
    anio_inicial = int(config["periodo"]["anio_inicial"])

    from importlib.metadata import version

    import xarray as xr
    from climada_petals.hazard.river_flood import RiverFlood

    out_dir.mkdir(parents=True, exist_ok=True)
    for prot, salida in pendientes.items():
        dph, frc = isimip_pair(paths.data / "isimip", prot)
        for nc in (dph, frc):
            if not verify_provenance(nc):
                raise RuntimeError(f"Insumo ISIMIP2a corrupto o sin procedencia: {nc}")
        with xr.open_dataset(dph) as ds:
            anios = select_years(sorted(set(ds["time"].dt.year.values.tolist())), anio_inicial)

        haz = RiverFlood.from_isimip_nc(
            dph_path=str(dph), frc_path=str(frc), centroids=cent, years=anios, origin=True
        )
        n_nan = sanitize_nan(haz)
        haz.write_hdf5(str(salida))
        write_provenance(
            salida,
            source=_FUENTE_RF,
            modelo="huellas anuales CaMa-Flood (máximo anual), forzamiento observado GSWP3",
            unidades="m (intensity) + fracción inundada (fraction)",
            proteccion=prot,
            anios=f"{anios[0]}-{anios[-1]}",
            n_eventos=len(anios),
            n_centroides=int(cent.size),
            n_celdas_nan_saneadas=n_nan,
            nota_frecuencia="frequency de petals sin significado aquí: eventos anuales observados",
            flddph_archivo=dph.name,
            flddph_sha256=_sha256(dph),
            fldfrc_archivo=frc.name,
            fldfrc_sha256=_sha256(frc),
            centroides_archivo=exp_path.name,
            centroides_sha256=_sha256(exp_path),
            climada_version=version("climada"),
            climada_petals_version=version("climada-petals"),
        )
        print(f"hazard fluvial ({prot}): {salida} ({len(anios)} años, {n_nan} celdas nan saneadas)")

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"haz_rf_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes=f"Hazard fluvial ISIMIP2a congelado ({', '.join(pendientes)}): sin RNG.",
    ).write(paths.manifests, paths.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
