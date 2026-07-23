"""Unit tests for the GloFAS fluvial footprints (CAL-RF-03, DC-CAL-HAZ-1)."""

import numpy as np
import pytest

xr = pytest.importorskip("xarray")

from impactcal.hazard.rf_glofas import (  # noqa: E402  (tras importorskip de xarray)
    bbox_desde_area,
    crop_flood_maps,
    to_centroid_grid,
)

RES = 0.05  # centroides "gruesos"
FINA = 0.01  # malla de inundación 5x más fina


def _depth(valores: np.ndarray):
    """(1, 10, 5) de profundidades sobre dos celdas-centroide apiladas en latitud."""
    lats = np.round(np.arange(-2, 8) * FINA, 4)  # -0.02 .. 0.07
    lons = np.round(np.arange(-2, 3) * FINA, 4)  # -0.02 .. 0.02
    return xr.DataArray(
        valores[None, :, :],
        dims=("year", "latitude", "longitude"),
        coords={"year": [2011], "latitude": lats, "longitude": lons},
    )


def test_agregacion_profundidad_y_fraccion():
    v = np.zeros((10, 5))
    v[0, :] = 2.0  # 5 subceldas mojadas, todas en la celda-centroide 0
    depth = _depth(v)
    lat_c = np.array([0.0, 0.05])
    lon_c = np.array([0.0, 0.0])

    intensidad, fraccion = to_centroid_grid(depth, lat_c, lon_c, RES)

    assert intensidad.shape == (1, 2)
    # profundidad = media sobre subceldas MOJADAS (no sobre las 25)
    assert intensidad[0, 0] == pytest.approx(2.0)
    # fracción = 5 mojadas de 25 subceldas
    assert fraccion[0, 0] == pytest.approx(5 / 25)
    # la segunda celda-centroide queda seca
    assert intensidad[0, 1] == 0.0 and fraccion[0, 1] == 0.0


def test_nan_cuenta_como_seco():
    """Sin cobertura de mapa JRC (NaN) = no es llanura de inundación = seco."""
    v = np.full((10, 5), np.nan)
    v[0, :2] = 1.0
    intensidad, fraccion = to_centroid_grid(_depth(v), np.array([0.0]), np.array([0.0]), RES)
    assert intensidad[0, 0] == pytest.approx(1.0)
    assert fraccion[0, 0] == pytest.approx(2 / 25)


def test_bbox_desde_area_orden_cds():
    assert bbox_desde_area([33, -118, 14, -86]) == {
        "lat_min": 14,
        "lat_max": 33,
        "lon_min": -118,
        "lon_max": -86,
    }


def test_crop_flood_maps_respeta_latitud_descendente():
    lats = np.arange(40, 9, -1.0)  # descendente, como los mapas JRC
    lons = np.arange(-130, -79, 1.0)
    fm = xr.DataArray(
        np.zeros((lats.size, lons.size)),
        dims=("latitude", "longitude"),
        coords={"latitude": lats, "longitude": lons},
    )
    out = crop_flood_maps(fm, bbox_desde_area([33, -118, 14, -86]))
    assert out.latitude.max() <= 33 and out.latitude.min() >= 14
    assert out.longitude.max() <= -86 and out.longitude.min() >= -118
    assert out.sizes["latitude"] > 0 and out.sizes["longitude"] > 0
