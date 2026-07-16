"""Static surge/riverflood input pinning (OQ-CAL-05, OQ-CAL-06 → OQ-CAL-15).

DEM: clips the pinned global SRTM15+ V2 to the buffered national polygon
(input of `TCSurgeBathtub.from_tc_winds`, CAL-SURGE-01/02) into `data/dem/`,
recording the derivation chain (global raster + marco sha256, buffer) in its
provenance. The buffer keeps shoreline/island topo-bathymetry so surge never
samples nodata at coastal centroids.

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
    "Recorte rectangular del raster global al bbox del polígono nacional (INEGI Marco "
    "Geoestadístico 00ent congelado, EPSG:4326) con buffer de {buffer} grados, lectura por "
    "ventana sin máscara ni remuestreo, GTiff LZW tiled (impactcal.hazard.freeze_inputs."
    "freeze_dem). Los huecos nodata dispersos del raster origen ({n_huecos} celdas, lagunas "
    "costeras e islas: Ojo de Liebre, Términos, Clarión) se rellenan por interpolación de "
    "vecinos (rasterio.fill.fillnodata) — cualquier nodata en el DEM hace que petals descarte "
    "centroides costeros en silencio (CAL-SURGE-02); la máscara exacta v0 agravaba esto en "
    "todo el litoral."
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
    dem_global: Path,
    marco_shp: Path,
    dest_dir: Path,
    *,
    buffer_grados: float = 0.1,
    force: bool = False,
) -> Path:
    """Crop the pinned global SRTM15+ to the buffered national bbox and freeze it.

    Rectangular window (no polygon mask) + neighbor-interpolation fill of the source
    raster's sparse nodata holes: the frozen DEM carries a real elevation in every cell,
    so surge generation can never sample nodata at wind-affected centroids — petals
    silently drops those (CAL-SURGE-02).
    """
    dest = dest_dir / "SRTM15+V2_Mexico.tif"
    if not force and verify_provenance(dest):
        return dest
    if not verify_provenance(marco_shp):
        raise RuntimeError(f"Marco Geoestadístico corrupto o sin procedencia: {marco_shp}")

    import geopandas as gpd
    import numpy as np
    import rasterio
    import rasterio.fill
    import rasterio.windows

    bounds = gpd.read_file(marco_shp).to_crs("EPSG:4326").total_bounds
    bounds += buffer_grados * np.array([-1.0, -1.0, 1.0, 1.0])
    with rasterio.open(dem_global) as src:
        window = rasterio.windows.from_bounds(*bounds, transform=src.transform)
        out = src.read(1, window=window)
        meta = src.meta | {
            "height": out.shape[0],
            "width": out.shape[1],
            "transform": src.window_transform(window),
            "driver": "GTiff",
            "compress": "lzw",
            "tiled": True,
        }
    n_huecos = int(np.isnan(out).sum())
    if n_huecos:
        out = rasterio.fill.fillnodata(out, mask=~np.isnan(out), max_search_distance=100)
    if np.isnan(out).any():
        raise RuntimeError(
            f"quedan {int(np.isnan(out).sum())} celdas nodata tras el relleno: "
            "huecos mayores que max_search_distance en el raster origen"
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dest, "w", **meta) as dst:
        dst.write(out, 1)
    write_provenance(
        dest,
        source=_FUENTE_DEM,
        derivacion=_DERIVACION_DEM.format(buffer=buffer_grados, n_huecos=n_huecos),
        buffer_grados=buffer_grados,
        n_huecos_rellenados=n_huecos,
        origen_global=str(dem_global.resolve()),
        origen_global_sha256=_sha256(dem_global),
        marco_00ent_sha256=_sha256(marco_shp),
    )
    return dest


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

    config = load_config(args.config)
    fuentes = config["fuentes_externas"]
    dem_global = Path(fuentes["dem_global"]).expanduser()
    isimip_dir = Path(fuentes["isimip_dir"]).expanduser()
    isimip_hist = Path(fuentes["isimip_hist"]).expanduser()
    data = ProjectPaths().data
    dem_dest_dir = data / "dem"
    isimip_dest_dir = data / "isimip"

    if args.modo == "verificar":
        estado = verify_inputs(dem_dest_dir / "SRTM15+V2_Mexico.tif", isimip_dir, isimip_dest_dir)
        for nombre, ok in estado.items():
            print(f"{'OK ' if ok else 'FALLA'} {nombre}")
        return 0 if all(estado.values()) else 1

    dem = freeze_dem(
        dem_global,
        data / "marco_geoestadistico" / "00ent.shp",
        dem_dest_dir,
        buffer_grados=float(config["hazard"]["dem_buffer_grados"]),
        force=args.forzar,
    )
    print(f"congelado: {dem}")
    for nc in pin_isimip(isimip_dir, force=args.forzar):
        print(f"pin en sitio: {nc}")
    for nc in freeze_isimip_hist(isimip_hist, isimip_dest_dir, force=args.forzar):
        print(f"congelado: {nc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
