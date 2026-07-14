"""Unit test for the state-assignment join (CAL-EXP-03; LitPop build not tested)."""

import geopandas as gpd
import numpy as np
from shapely.geometry import box

from impactcal.exposure.litpop import assign_states


def test_assign_states_within_and_nearest():
    estados = gpd.GeoDataFrame(
        {"CVEGEO": ["01", "02"]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)],
        crs="EPSG:4326",
    )
    lat = np.array([0.5, 0.5, 0.5, 1.0])  # last: on the shared corner (boundary)
    lon = np.array([0.5, 1.5, 2.6, 1.0])  # third: outside both, nearest to 02
    cve = assign_states(lat, lon, estados)
    assert list(cve[:3]) == ["01", "02", "02"]
    assert cve[3] in {"01", "02"}  # boundary point: single, deterministic-first match
