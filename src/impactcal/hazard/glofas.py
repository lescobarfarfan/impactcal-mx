"""GloFAS-ERA5 raw discharge ingestion (CAL-RF-01 fase 2: años sin ISIMIP2a).

Downloads daily river discharge (dis24) from the CEMS Early Warning Data
Store (dataset `cems-glofas-historical`, GloFAS-ERA5 reanalysis 1979-present,
doi:10.24381/cds.a4fdd6b9) over the Mexico bbox, one NetCDF per year, into
`data/glofas/crudos/` with `_procedencia.json` recording the full request.
Requires the ECMWF token in `~/.cdsapirc` (shared with CDS) and the EWDS
dataset licences accepted. Footprint computation (petals `rf_glofas`) is a
separate, later step.

CLI::

    python -m impactcal.hazard.glofas [--modo descargar|verificar] [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from impactcal.infra.config import load_config
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import verify_provenance, write_provenance

EWDS_URL = "https://ewds.climate.copernicus.eu/api"
DATASET = "cems-glofas-historical"

_FUENTE = (
    "GloFAS-ERA5 river discharge reanalysis (CEMS Early Warning Data Store, "
    "doi:10.24381/cds.a4fdd6b9) [ref? -> REFERENCES §99]"
)


def build_request(anio: int, cfg: dict[str, Any]) -> dict[str, Any]:
    """EWDS retrieval request for one full year of daily dis24 over the bbox."""
    return {
        "system_version": [cfg["system_version"]],
        "hydrological_model": [cfg["hydrological_model"]],
        "product_type": [cfg["product_type"]],
        "variable": ["river_discharge_in_the_last_24_hours"],
        "hyear": [str(anio)],
        "hmonth": [f"{m:02d}" for m in range(1, 13)],
        "hday": [f"{d:02d}" for d in range(1, 32)],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": cfg["area"],
    }


def _dest_name(anio: int, cfg: dict[str, Any]) -> str:
    return f"glofas-era5_{cfg['system_version']}_dis24_mexico_{anio}.nc"


def download_glofas(cfg: dict[str, Any], dest_dir: Path, *, force: bool = False) -> list[Path]:
    """Download one NetCDF per configured year, idempotently, with provenance."""
    import cdsapi

    key = dict(
        line.split(": ", 1)
        for line in Path.home().joinpath(".cdsapirc").read_text().splitlines()
        if ": " in line
    )["key"].strip()
    client = cdsapi.Client(url=EWDS_URL, key=key)

    out = []
    for anio in cfg["anios"]:
        dest = dest_dir / _dest_name(anio, cfg)
        if not force and verify_provenance(dest):
            out.append(dest)
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        request = build_request(anio, cfg)
        client.retrieve(DATASET, request, str(dest))
        write_provenance(dest, source=_FUENTE, dataset=DATASET, request=request)
        out.append(dest)
    return out


def verify_glofas(cfg: dict[str, Any], dest_dir: Path) -> dict[str, bool]:
    """Checksum verification of the downloaded yearly files (no downloading)."""
    return {
        _dest_name(anio, cfg): verify_provenance(dest_dir / _dest_name(anio, cfg))
        for anio in cfg["anios"]
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--modo", choices=["descargar", "verificar"], default="descargar")
    parser.add_argument("--forzar", action="store_true", help="re-descarga aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    cfg = load_config(args.config)["glofas"]
    dest_dir = ProjectPaths().data / "glofas" / "crudos"

    if args.modo == "verificar":
        estado = verify_glofas(cfg, dest_dir)
        for nombre, ok in estado.items():
            print(f"{'OK ' if ok else 'FALLA'} {nombre}")
        return 0 if all(estado.values()) else 1

    for p in download_glofas(cfg, dest_dir, force=args.forzar):
        print(f"descargado: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
