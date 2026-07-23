"""GloFAS-ERA5 raw discharge ingestion (CAL-RF-01 fase 2: años sin ISIMIP2a).

Downloads daily river discharge (dis24) from the CEMS Early Warning Data
Store (dataset `cems-glofas-historical`, GloFAS-ERA5 reanalysis 1979-present,
doi:10.24381/cds.a4fdd6b9) over the Mexico bbox, one NetCDF per year, into
`data/glofas/crudos/` with `_procedencia.json` recording the full request.
Requires the ECMWF token in `~/.cdsapirc` (shared with CDS) and the EWDS
dataset licences accepted.

`--modo auxiliares` freezes the static inputs of the petals `rf_glofas`
inundation pipeline (OQ-CAL-17) into `data/glofas/auxiliares/`: the merged
JRC global flood hazard maps, the FLOPROS protection-standards shapefile and
the precomputed GloFAS Gumbel fits. The footprint computation itself
(discharge → return period → inundation, 2011-2015) is the remaining step of
OQ-CAL-17.

CLI::

    python -m impactcal.hazard.glofas [--modo descargar|verificar|auxiliares] [--forzar]
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

_FUENTE_JRC = (
    "JRC global river flood hazard maps rp{10,20,50,100,200,500}, fusionados por petals "
    "setup_flood_hazard_maps [ref? -> REFERENCES §99]"
)
_FUENTE_FLOPROS = (
    "FLOPROS: an evolving global database of flood protection standards "
    "(doi:10.5194/nhess-16-1049-2016) [ref? -> REFERENCES §99]"
)
_FUENTE_GUMBEL = (
    "Ajustes Gumbel precomputados de descarga GloFAS 1979-2023 (ETH Research Collection, "
    "hdl:20.500.11850/726304, dato companion de petals rf_glofas) [ref? -> REFERENCES §99]"
)

# La URL hardcodeada en petals 6.1.0 (research-collection viejo) hoy devuelve una página HTML;
# bitstream resuelto vía la API DSpace del handle. Si ETH vuelve a migrar, el chequeo MD5 de
# abajo falla en voz alta y esta URL se re-resuelve.
#
# EDICIÓN 1979-2023, no la 1979-2015 que referencia petals (OQ-CAL-17c, decidido con datos):
# el fit 1979-2015 vive en la malla GloFAS v3 de 0.1° y `transform_ops.return_period` reindexa
# el fit sobre las coordenadas de la descarga con tolerancia 1e-3° y `assert_no_fill_value`.
# Nuestra descarga congelada es GloFAS-ERA5 **v4.0 a 0.05°** (CAL-RF-03), así que el fit de
# 0.1° falla en voz alta ("Reindexing 'loc' to 'dis24' exceeds tolerance"). El fit 1979-2023
# está en la malla v4.0 de 0.05° (101 MB vs 10 MB = 4× celdas) y es además el consistente en
# versión con la descarga.
GUMBEL_FIT_URL = (
    "https://www.research-collection.ethz.ch/server/api/core/bitstreams/"
    "ee5a1594-fd1c-490b-9e78-710c4bdd8709/content"
)
GUMBEL_FIT_MD5 = "b18e8839e07acbc69ff8e8c26e0c7015"
GUMBEL_FIT_HANDLE = "20.500.11850/726304"


def download_aux(dest_dir: Path, *, force: bool = False) -> list[Path]:
    """Freeze the static rf_glofas inputs (JRC maps, Gumbel fits, FLOPROS) with provenance."""
    from climada_petals.hazard.rf_glofas import setup

    dest_dir.mkdir(parents=True, exist_ok=True)
    out = []

    flood_nc = dest_dir / "flood-maps.nc"
    if force or not verify_provenance(flood_nc):
        setup.setup_flood_hazard_maps(dest_dir / "flood-maps-tif", output_dir=dest_dir)
        write_provenance(flood_nc, source=_FUENTE_JRC, urls=setup.JRC_FLOOD_HAZARD_MAPS)
    out.append(flood_nc)

    gumbel_nc = dest_dir / "gumbel-fit.nc"
    if force or not verify_provenance(gumbel_nc):
        import hashlib

        import requests

        data = requests.get(GUMBEL_FIT_URL, timeout=600).content
        md5 = hashlib.md5(data).hexdigest()
        if md5 != GUMBEL_FIT_MD5:
            raise RuntimeError(
                f"gumbel-fit.nc descargado no coincide con el MD5 del repositorio ETH "
                f"({md5} != {GUMBEL_FIT_MD5}): ¿URL rota otra vez? Re-resolver vía la API "
                f"DSpace del handle {GUMBEL_FIT_HANDLE}."
            )
        gumbel_nc.write_bytes(data)
        write_provenance(
            gumbel_nc,
            source=_FUENTE_GUMBEL,
            url=GUMBEL_FIT_URL,
            handle=GUMBEL_FIT_HANDLE,
            md5_repositorio=GUMBEL_FIT_MD5,
            edicion="1979-2023 (malla v4.0 0.05°, consistente con la descarga; OQ-CAL-17c)",
        )
    out.append(gumbel_nc)

    flopros_dir = dest_dir / "FLOPROS_shp_V1"
    shps = sorted(flopros_dir.glob("*.shp"))
    if force or not shps or not verify_provenance(shps[0]):
        setup.download_flopros_database(dest_dir)
        (shp,) = sorted(flopros_dir.glob("*.shp"))
        write_provenance(shp, source=_FUENTE_FLOPROS, url=setup.FLOPROS_DATA)
        shps = [shp]
    out.append(shps[0])
    return out


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
    parser.add_argument(
        "--modo", choices=["descargar", "verificar", "auxiliares"], default="descargar"
    )
    parser.add_argument("--forzar", action="store_true", help="re-descarga aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    cfg = load_config(args.config)["glofas"]
    dest_dir = ProjectPaths().data / "glofas" / "crudos"

    if args.modo == "auxiliares":
        for p in download_aux(ProjectPaths().data / "glofas" / "auxiliares", force=args.forzar):
            print(f"congelado: {p}")
        return 0

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
