"""Unit test for the GloFAS-ERA5 request builder (network calls not tested)."""

from impactcal.hazard.glofas import build_request

_CFG = {
    "system_version": "version_4_0",
    "hydrological_model": "lisflood",
    "product_type": "consolidated",
    "area": [33, -118, 14, -86],
}


def test_build_request():
    req = build_request(2011, _CFG)
    assert req["hyear"] == ["2011"]
    assert len(req["hmonth"]) == 12 and req["hmonth"][0] == "01"
    assert len(req["hday"]) == 31 and req["hday"][-1] == "31"
    assert req["area"] == [33, -118, 14, -86]
    assert req["variable"] == ["river_discharge_in_the_last_24_hours"]
