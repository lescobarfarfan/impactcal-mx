"""IBTrACS v04r01 raw ingestion and per-storm index (CAL-WIND-01 input).

Freezes the raw basin CSVs (EP + NA) already downloaded in the climateCCR repo
into `data/ibtracs/crudos/` (CAL-GEN-02/12), and builds a per-storm index
(SID, SEASON, NAME, date span, near-Mexico flag) consumed by the crosswalk
(DC-XWALK-1). Also freezes the CLIMADA-cached `IBTrACS.ALL.v04r01.nc` (the
file `TCTracks.from_ibtracs_netcdf` reads) as-is into the same directory,
recording its internal `date_created` (OQ-CAL-15). Wind-field generation
itself (`TCTracks`/`TropCyclone`) is a separate step.

CLI::

    python -m impactcal.hazard.ibtracs [--modo ingerir|verificar] [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from impactcal.infra.config import load_config
from impactcal.infra.freeze import freeze_copy
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import verify_provenance

CRUDOS = (
    "ibtracs.EP.list.v04r01.csv",
    "ibtracs.NA.list.v04r01.csv",
)

NC_CACHE = "IBTrACS.ALL.v04r01.nc"

_FUENTE = "NOAA NCEI IBTrACS v04r01, cuencas EP+NA [Knapp2010][IBTrACSv04r01]"

_FUENTE_NC = (
    "NOAA NCEI IBTrACS v04r01, caché CLIMADA de TCTracks.from_ibtracs_netcdf "
    "[Knapp2010][IBTrACSv04r01]"
)

_NC_ATTRS = ("product_version", "date_created", "time_coverage_end", "metadata_link")

_USECOLS = ["SID", "SEASON", "NAME", "ISO_TIME", "LAT", "LON", "TRACK_TYPE"]


def ingest_ibtracs(source_dir: Path, dest_dir: Path, *, force: bool = False) -> list[Path]:
    """Freeze the IBTrACS basin CSVs into `dest_dir` with provenance."""
    return [
        freeze_copy(source_dir / nombre, dest_dir, source=_FUENTE, force=force) for nombre in CRUDOS
    ]


def ingest_ibtracs_nc(nc_src: Path, dest_dir: Path, *, force: bool = False) -> Path:
    """Freeze the CLIMADA-cached IBTrACS netCDF as-is, pinning its internal date."""
    import xarray as xr

    attrs = xr.open_dataset(nc_src).attrs
    extra = {k: str(attrs[k]) for k in _NC_ATTRS if k in attrs}
    return freeze_copy(nc_src, dest_dir, source=_FUENTE_NC, force=force, **extra)


def verify_ibtracs(dest_dir: Path) -> dict[str, bool]:
    """Checksum verification of the frozen raw files (no copying)."""
    return {nombre: verify_provenance(dest_dir / nombre) for nombre in (*CRUDOS, NC_CACHE)}


def load_storm_index(
    crudos_dir: Path,
    *,
    season_min: int = 2000,
    bbox: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Per-storm index from the frozen basin CSVs.

    Returns one row per SID: `sid, season, name, fecha_inicio, fecha_fin,
    toca_mexico` (any track point inside `bbox`; True for every storm when no
    bbox is given). Spur track entries are dropped; storms present in both
    basin files (basin crossers) collapse to a single row.
    """
    frames = []
    for nombre in CRUDOS:
        ruta = crudos_dir / nombre
        df = pd.read_csv(ruta, skiprows=[1], usecols=_USECOLS, dtype=str, na_filter=False)
        frames.append(df)
    puntos = pd.concat(frames, ignore_index=True)
    puntos = puntos[puntos["TRACK_TYPE"].str.strip().str.lower() != "spur"]
    puntos["season"] = pd.to_numeric(puntos["SEASON"], errors="coerce")
    puntos = puntos[puntos["season"] >= season_min]
    puntos["iso_time"] = pd.to_datetime(puntos["ISO_TIME"], errors="coerce")
    puntos["lat"] = pd.to_numeric(puntos["LAT"], errors="coerce")
    puntos["lon"] = pd.to_numeric(puntos["LON"], errors="coerce")
    if bbox is not None:
        puntos["en_bbox"] = puntos["lat"].between(bbox["lat_min"], bbox["lat_max"]) & puntos[
            "lon"
        ].between(bbox["lon_min"], bbox["lon_max"])
    else:
        puntos["en_bbox"] = True

    def _nombre(serie: pd.Series) -> str:
        con_nombre = serie[~serie.isin(["NOT_NAMED", "UNNAMED", ""])]
        return con_nombre.iloc[0] if len(con_nombre) else "NOT_NAMED"

    index = (
        puntos.groupby("SID")
        .agg(
            season=("season", "min"),
            name=("NAME", _nombre),
            fecha_inicio=("iso_time", "min"),
            fecha_fin=("iso_time", "max"),
            toca_mexico=("en_bbox", "any"),
        )
        .reset_index()
        .rename(columns={"SID": "sid"})
    )
    index["season"] = index["season"].astype(int)
    return index.sort_values(["season", "fecha_inicio", "sid"]).reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--modo", choices=["ingerir", "verificar"], default="ingerir")
    parser.add_argument("--forzar", action="store_true", help="re-copia aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()
    source_dir = Path(config["fuentes_externas"]["ibtracs_crudos"]).expanduser()
    dest_dir = paths.data / "ibtracs" / "crudos"

    if args.modo == "verificar":
        estado = verify_ibtracs(dest_dir)
        for nombre, ok in estado.items():
            print(f"{'OK ' if ok else 'FALLA'} {nombre}")
        return 0 if all(estado.values()) else 1

    frozen = ingest_ibtracs(source_dir, dest_dir, force=args.forzar)
    nc_src = Path(config["fuentes_externas"]["ibtracs_nc"]).expanduser()
    frozen.append(ingest_ibtracs_nc(nc_src, dest_dir, force=args.forzar))
    for p in frozen:
        print(f"congelado: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
