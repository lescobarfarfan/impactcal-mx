"""Static surge/riverflood input pinning (OQ-CAL-05, OQ-CAL-06 → OQ-CAL-15).

DEM: freezes the Mexico-clipped SRTM15+ V2 GeoTIFF (input of
`TCSurgeBathtub.from_tc_winds`, CAL-SURGE-01) into `data/dem/`, recording the
derivation chain (global raster sha256 + clip notebook) in its provenance.

ISIMIP2b RCP flood files: pinned **in place** (sidecar next to each `.nc`),
not copied — RCP projections (2006–2100, GCM weather) cannot serve the
2000–2015 observed-loss calibration (CAL-RF-01); pinning records exactly
which files were evaluated.

ISIMIP2a historical flood files (observed GSWP3 forcing, 1971–2010; ISIMIP
DerivedOutputData/Zimmer2023, doi:10.48364/ISIMIP.303619): **frozen** into
`data/isimip/` — these are the actual RF calibration inputs (CAL-GEN-12).

CLI::

    python -m impactcal.hazard.freeze_inputs [--modo ingerir|verificar] [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from impactcal.infra.config import load_config
from impactcal.infra.freeze import freeze_copy
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance

_FUENTE_DEM = "SRTM15+ V2 (15 arcsec global), recorte México [Tozer2019]"

_DERIVACION_DEM = (
    "Recorte del raster global al polígono nacional (INEGI Marco Geoestadístico 00ent, "
    "EPSG:4326) vía rasterio.mask, sin remuestreo, GTiff LZW tiled; notebook "
    "Procesa_Raster_Altitud.ipynb junto al artefacto de origen."
)

_FUENTE_ISIMIP = (
    "Inundación fluvial ISIMIP2b / CaMa-Flood, flood-processing de S. Willner "
    "(doi:10.5281/zenodo.1241051) [Sauer2021-ref?]"
)

_ISIMIP_ATTRS = (
    "ensemble_name",
    "scenario",
    "ghm",
    "gcm",
    "cama_flood_version",
    "soc",
    "fit",
    "fit_scenario",
    "citation",
    "flood_processing_version",
    "created_at",
)

_NOTA_ISIMIP = (
    "Escenario RCP 2006-2100 con clima GCM: no cubre 2000-2005 ni corresponde a años "
    "observados — insumo RF para la calibración histórica pendiente de decisión."
)

_FUENTE_ISIMIP2A = (
    "Inundación fluvial ISIMIP2a, forzamiento observado, CaMa-Flood; ISIMIP "
    "DerivedOutputData/Zimmer2023 (doi:10.48364/ISIMIP.303619) [Sauer2021-ref?]"
)


def _isimip_extra(nc: Path) -> dict[str, str]:
    """Provenance extras read from a flood NetCDF's global attrs + time axis."""
    import xarray as xr

    ds = xr.open_dataset(nc)
    extra = {k: str(ds.attrs[k]) for k in _ISIMIP_ATTRS if k in ds.attrs}
    t = ds["time"].values
    extra["cobertura_temporal"] = f"{t[0]}..{t[-1]}"
    ds.close()
    return extra


def freeze_dem(
    dem_mx: Path, dem_global: Path | None, dest_dir: Path, *, force: bool = False
) -> Path:
    """Freeze the Mexico DEM clip with its derivation chain in the provenance."""
    dest = dest_dir / dem_mx.name
    if not force and verify_provenance(dest):
        return dest
    extra: dict[str, str] = {"derivacion": _DERIVACION_DEM}
    if dem_global is not None and dem_global.exists():
        extra["origen_global"] = str(dem_global.resolve())
        extra["origen_global_sha256"] = _sha256(dem_global)
    return freeze_copy(dem_mx, dest_dir, source=_FUENTE_DEM, force=force, **extra)


def isimip_files(isimip_dir: Path) -> list[Path]:
    """The in-hand ISIMIP depth/fraction NetCDFs, sorted by name."""
    return sorted(
        [*isimip_dir.glob("*_flddph_*.nc"), *isimip_dir.glob("*_fldfrc_*.nc")],
        key=lambda p: p.name,
    )


def pin_isimip(isimip_dir: Path, *, force: bool = False) -> list[Path]:
    """Write in-place provenance sidecars for the ISIMIP2b RCP flood NetCDFs."""
    pinned = []
    for nc in isimip_files(isimip_dir):
        if not force and verify_provenance(nc):
            pinned.append(nc)
            continue
        write_provenance(nc, source=_FUENTE_ISIMIP, nota=_NOTA_ISIMIP, **_isimip_extra(nc))
        pinned.append(nc)
    return pinned


def isimip_hist_files(src_dir: Path) -> list[Path]:
    """The ISIMIP2a historical depth/fraction NetCDFs, sorted by name."""
    return sorted(
        [*src_dir.glob("cama-flood_*_flddph_*.nc4"), *src_dir.glob("cama-flood_*_fldfrc_*.nc4")],
        key=lambda p: p.name,
    )


def freeze_isimip_hist(src_dir: Path, dest_dir: Path, *, force: bool = False) -> list[Path]:
    """Freeze the ISIMIP2a observed-forcing flood files (RF calibration inputs)."""
    frozen = []
    for nc in isimip_hist_files(src_dir):
        dest = dest_dir / nc.name
        if not force and verify_provenance(dest):
            frozen.append(dest)
            continue
        frozen.append(
            freeze_copy(nc, dest_dir, source=_FUENTE_ISIMIP2A, force=force, **_isimip_extra(nc))
        )
    return frozen


def verify_inputs(dem_dest: Path, isimip_dir: Path, isimip_frozen_dir: Path) -> dict[str, bool]:
    """Checksum verification of the frozen DEM, RCP pins, and frozen ISIMIP2a files."""
    estado = {dem_dest.name: verify_provenance(dem_dest)}
    for nc in isimip_files(isimip_dir):
        estado[nc.name] = verify_provenance(nc)
    for nc in isimip_hist_files(isimip_frozen_dir):
        estado[nc.name] = verify_provenance(nc)
    return estado


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--modo", choices=["ingerir", "verificar"], default="ingerir")
    parser.add_argument("--forzar", action="store_true", help="re-pin aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    fuentes = load_config(args.config)["fuentes_externas"]
    dem_mx = Path(fuentes["dem_mexico"]).expanduser()
    dem_global = Path(fuentes["dem_global"]).expanduser()
    isimip_dir = Path(fuentes["isimip_dir"]).expanduser()
    isimip_hist = Path(fuentes["isimip_hist"]).expanduser()
    data = ProjectPaths().data
    dem_dest_dir = data / "dem"
    isimip_dest_dir = data / "isimip"

    if args.modo == "verificar":
        estado = verify_inputs(dem_dest_dir / dem_mx.name, isimip_dir, isimip_dest_dir)
        for nombre, ok in estado.items():
            print(f"{'OK ' if ok else 'FALLA'} {nombre}")
        return 0 if all(estado.values()) else 1

    dem = freeze_dem(dem_mx, dem_global, dem_dest_dir, force=args.forzar)
    print(f"congelado: {dem}")
    for nc in pin_isimip(isimip_dir, force=args.forzar):
        print(f"pin en sitio: {nc}")
    for nc in freeze_isimip_hist(isimip_hist, isimip_dest_dir, force=args.forzar):
        print(f"congelado: {nc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
