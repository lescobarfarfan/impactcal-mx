"""Unit + end-to-end tests for the v0 crosswalk (DC-XWALK-1, CAL-XWALK-01/02)."""

import pandas as pd
import pytest

from impactcal.hazard.ibtracs import CRUDOS, load_storm_index
from impactcal.target.crosswalk import build_crosswalk, extract_storm_names

_CONFIG = {
    "crosswalk": {
        "version": "v0-test",
        "subtipos_ciclonicos": ["CT", "MT", "MF"],
        "subtipos_fluviales": ["LLUV", "INUND"],
        "buffer_dias": 3,
        "bbox_mexico": {"lat_min": 12.0, "lat_max": 35.0, "lon_min": -120.0, "lon_max": -84.0},
    }
}

_IBTRACS_HEADER = "SID,SEASON,NAME,ISO_TIME,LAT,LON,TRACK_TYPE\n ,Year, , ,deg_n,deg_e, \n"

_EP_ROWS = (
    "EP182014,2014,ODILE,2014-09-10 00:00:00,15.0,-105.0,main\n"
    "EP182014,2014,ODILE,2014-09-18 00:00:00,28.0,-112.0,main\n"
    "EP182014,2014,ODILE,2014-09-18 06:00:00,28.5,-112.5,spur\n"
    "EP162014,2014,NORBERT,2014-09-02 00:00:00,18.0,-108.0,main\n"
    "EP162014,2014,NORBERT,2014-09-08 00:00:00,25.0,-115.0,main\n"
    "EP072014,2014,GENEVIEVE,2014-08-01 00:00:00,15.0,-140.0,main\n"
    "EP091999,1999,GREG,1999-09-05 00:00:00,18.0,-106.0,main\n"
)

_NA_ROWS = (
    "AL042014,2014,DOLLY,2014-08-20 00:00:00,23.0,-97.0,main\n"
    "AL042014,2014,DOLLY,2014-08-21 12:00:00,24.0,-98.5,main\n"
)


@pytest.fixture
def storm_index(tmp_path):
    (tmp_path / CRUDOS[0]).write_text(_IBTRACS_HEADER + _EP_ROWS)
    (tmp_path / CRUDOS[1]).write_text(_IBTRACS_HEADER + _NA_ROWS)
    return load_storm_index(tmp_path, season_min=2000, bbox=_CONFIG["crosswalk"]["bbox_mexico"])


def test_extract_storm_names():
    assert extract_storm_names("Ciclón Odile") == ["ODILE"]
    assert extract_storm_names("Huracán Ingrid y Tormenta Tropical Manuel") == [
        "INGRID",
        "MANUEL",
    ]
    assert extract_storm_names("Depresión Tropical Once-E") == ["ELEVEN-E"]
    assert extract_storm_names("") == []
    assert extract_storm_names("Ciclón tropical") == []


def test_load_storm_index(storm_index):
    assert set(storm_index["sid"]) == {"EP182014", "EP162014", "EP072014", "AL042014"}
    odile = storm_index.set_index("sid").loc["EP182014"]
    assert odile["name"] == "ODILE" and odile["season"] == 2014
    assert odile["fecha_fin"] == pd.Timestamp("2014-09-18 00:00:00")  # spur row dropped
    assert bool(odile["toca_mexico"])
    assert not bool(storm_index.set_index("sid").loc["EP072014", "toca_mexico"])


def _eventos() -> pd.DataFrame:
    columnas = [
        "evento_id",
        "anio",
        "subtipo",
        "en_alcance_climatico",
        "nombre_evento",
        "estados",
        "fecha_inicio",
        "fecha_fin",
    ]
    filas = [
        # Named CT → match by nombre; two states.
        (
            "E1",
            "2014",
            "CT",
            "si",
            "Ciclón Odile",
            "Baja California Sur|Sonora",
            "2014-09-14",
            "2014-09-17",
        ),
        # Unnamed CT → date fallback, single candidate (NORBERT).
        ("E2", "2014", "CT", "si", "", "Tamaulipas", "2014-09-04", "2014-09-05"),
        # LLUV inside a matched storm window → ciclonica (inland CDMX case).
        ("E3", "2014", "LLUV", "si", "", "Ciudad de México", "2014-09-15", "2014-09-16"),
        # INUND in a year with no matched storms → fluvial independiente.
        ("E4", "2013", "INUND", "si", "", "Tabasco", "2013-11-01", "2013-11-05"),
        # Named CT with no IBTrACS match and no dates → flagged, still ciclonica.
        ("E5", "2014", "CT", "si", "Huracán Fantasma", "Colima", "", ""),
        # INUND far from any 2014 storm window → mixes with ODILE in Sonora.
        ("E6", "2014", "INUND", "si", "", "Sonora", "2014-06-01", "2014-06-02"),
        # Out of the crosswalk universe: not climate / not ciclón-fluvial subtype.
        ("E7", "2014", "SIS", "no", "", "Oaxaca", "2014-01-01", "2014-01-01"),
        ("E8", "2014", "SEQ", "si", "", "Zacatecas", "2014-01-01", "2014-12-31"),
    ]
    return pd.DataFrame(filas, columns=columnas)


def test_build_crosswalk_end_to_end(storm_index):
    xwalk, match, resumen = build_crosswalk(_eventos(), storm_index, _CONFIG)

    assert list(xwalk.columns) == [
        "anio",
        "cve_ent",
        "sids_viento",
        "sids_cono_lluvia",
        "familia_asignada",
        "flag_revision",
        "regla_aplicada",
        "version_crosswalk",
    ]
    assert (xwalk["version_crosswalk"] == "v0-test").all()
    assert (xwalk["sids_cono_lluvia"] == "").all()  # v1 pending (OQ-CAL-01)

    filas = {(r.anio, r.cve_ent): r for r in xwalk.itertuples()}
    # Odile by name in BCS (03); Tamaulipas (28) by date fallback → NORBERT.
    assert filas[(2014, "03")].sids_viento == "EP182014"
    assert filas[(2014, "03")].familia_asignada == "ciclonica"
    assert filas[(2014, "28")].sids_viento == "EP162014"
    assert filas[(2014, "28")].regla_aplicada == "ct_reportado"
    # CDMX (09): rain inside storm window → ciclonica.
    assert filas[(2014, "09")].familia_asignada == "ciclonica"
    assert filas[(2014, "09")].regla_aplicada == "lluvia_en_ventana_tormenta"
    # Tabasco 2013 (27): no storm that year → fluvial.
    assert filas[(2013, "27")].familia_asignada == "fluvial"
    assert filas[(2013, "27")].regla_aplicada == "fluvial_independiente"
    # Colima (06): unmatched named CT → flagged, no SID.
    assert filas[(2014, "06")].sids_viento == ""
    assert "ct_sin_sid" in filas[(2014, "06")].flag_revision
    assert "nombre_sin_sid" in filas[(2014, "06")].flag_revision
    # Sonora (26): ODILE + out-of-window INUND → mixta_flag.
    assert filas[(2014, "26")].familia_asignada == "mixta_flag"
    # Out-of-universe events never enter.
    assert (2014, "20") not in filas and (2014, "32") not in filas

    metodos = match.set_index("evento_id")["metodo_match"]
    assert metodos["E1"] == "nombre"
    assert metodos["E2"] == "fechas"
    assert metodos["E5"] == "sin_match"
    assert resumen["n_eventos_ct"] == 3
