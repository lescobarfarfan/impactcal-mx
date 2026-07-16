"""Unit + end-to-end tests for frozen-input ingestion (CAL-GEN-02/12)."""

import json

import pytest

from impactcal.infra.freeze import freeze_copy
from impactcal.infra.provenance import verify_provenance, write_provenance
from impactcal.target.cenapred import CONSOLIDADOS, ingest_cenapred, verify_cenapred


def _sidecar(artifact):
    return json.loads(
        artifact.with_name(artifact.name + "._procedencia.json").read_text(encoding="utf-8")
    )


def test_freeze_copy_roundtrip(tmp_path):
    src = tmp_path / "origen" / "dato.csv"
    src.parent.mkdir()
    src.write_text("a,b\n1,2\n")
    dest_dir = tmp_path / "data" / "fuente"

    dest = freeze_copy(src, dest_dir, source="unit-test")
    assert dest.read_text() == "a,b\n1,2\n"
    assert verify_provenance(dest)

    # Idempotent: intact destination is not rewritten.
    antes = dest.stat().st_mtime_ns
    assert freeze_copy(src, dest_dir, source="unit-test") == dest
    assert dest.stat().st_mtime_ns == antes

    # Corrupted destination is restored on the next pass.
    dest.write_text("corrupto")
    freeze_copy(src, dest_dir, source="unit-test")
    assert dest.read_text() == "a,b\n1,2\n" and verify_provenance(dest)


def test_freeze_copy_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        freeze_copy(tmp_path / "no_existe.csv", tmp_path / "data", source="unit-test")


def test_ingest_cenapred_end_to_end(tmp_path):
    source = tmp_path / "climateCCR"
    source.mkdir()
    for nombre in CONSOLIDADOS:
        (source / nombre).write_text(f"columna\n{nombre}\n")
    dest = tmp_path / "data" / "cenapred" / "consolidados"

    frozen = ingest_cenapred(source, dest)
    assert [p.name for p in frozen] == list(CONSOLIDADOS)
    assert all(verify_cenapred(dest).values())

    (dest / CONSOLIDADOS[0]).write_text("alterado\n")
    assert not verify_cenapred(dest)[CONSOLIDADOS[0]]


def test_ingest_ibtracs_nc(tmp_path):
    import xarray as xr

    from impactcal.hazard.ibtracs import ingest_ibtracs_nc

    nc = tmp_path / "IBTrACS.ALL.v04r01.nc"
    xr.Dataset(
        attrs={"product_version": "v04r01", "date_created": "2025-08-22 00:25:10"}
    ).to_netcdf(nc)

    dest = ingest_ibtracs_nc(nc, tmp_path / "data")
    assert verify_provenance(dest)
    assert _sidecar(dest)["date_created"] == "2025-08-22 00:25:10"


def test_freeze_inputs_end_to_end(tmp_path):
    import numpy as np
    import xarray as xr

    from impactcal.hazard.freeze_inputs import (
        freeze_dem,
        freeze_isimip_hist,
        pin_isimip,
        verify_inputs,
    )

    origen = tmp_path / "origen"
    origen.mkdir()
    dem_global = origen / "SRTM15+V2.tiff"
    dem_global.write_bytes(b"tif-global")
    nc = origen / "26_flddph_150arcsec_matsiro_hadgem2-es_0.nc"
    xr.Dataset(
        {"flddph": ("time", [0.0])},
        coords={"time": [np.datetime64("2006-07-02", "ns")]},
        attrs={"ensemble_name": "isimip2b", "scenario": "rcp26"},
    ).to_netcdf(nc)
    hist = origen / "cama-flood_matsiro_gswp3_flddph_none_150arcsec.nc4"
    xr.Dataset(
        {"flddph": ("time", [0.0])},
        coords={"time": [np.datetime64("1971-07-02", "ns")]},
    ).to_netcdf(hist)

    # freeze_dem: an intact frozen clip short-circuits before touching rasterio/geopandas.
    dem_dest_dir = tmp_path / "data" / "dem"
    dem_dest_dir.mkdir(parents=True)
    dem_previo = dem_dest_dir / "SRTM15+V2_Mexico.tif"
    dem_previo.write_bytes(b"tif-recorte")
    write_provenance(dem_previo, source="test")
    dem_dest = freeze_dem(dem_global, origen / "00ent.shp", dem_dest_dir)
    assert dem_dest == dem_previo
    assert _sidecar(dem_dest)["fuente"] == "test"  # no reescrito

    # A re-clip demands a frozen marco with provenance.
    with pytest.raises(RuntimeError, match="Marco"):
        freeze_dem(dem_global, origen / "00ent.shp", dem_dest_dir, force=True)

    assert pin_isimip(origen) == [nc]
    assert _sidecar(nc)["scenario"] == "rcp26"

    isimip_dest = tmp_path / "data" / "isimip"
    (frozen_hist,) = freeze_isimip_hist(origen, isimip_dest)
    assert verify_provenance(frozen_hist)
    assert _sidecar(frozen_hist)["cobertura_temporal"].startswith("1971")

    assert all(verify_inputs(dem_dest, origen, isimip_dest).values())

    # Idempotent: the in-place pin is not rewritten on a second pass.
    antes = nc.with_name(nc.name + "._procedencia.json").stat().st_mtime_ns
    pin_isimip(origen)
    assert nc.with_name(nc.name + "._procedencia.json").stat().st_mtime_ns == antes
