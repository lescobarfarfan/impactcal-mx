"""Unit + end-to-end tests for the v1 crosswalk (DC-XWALK-1, CAL-XWALK-01/02)."""

import pandas as pd
import pytest

from impactcal.hazard.ibtracs import CRUDOS, load_storm_index
from impactcal.target.crosswalk import build_crosswalk, extract_storm_names

_CONFIG = {
    "impacto": {"v_thresh": 25.7},
    "crosswalk": {
        "version": "v1-test",
        "umbral_lluvia_mm": 80.0,
        "subtipos_ciclonicos": ["CT", "MT", "MF"],
        "subtipos_fluviales": ["LLUV", "INUND"],
        "buffer_dias": 3,
        "bbox_mexico": {"lat_min": 12.0, "lat_max": 35.0, "lon_min": -120.0, "lon_max": -84.0},
    },
}

_IBTRACS_HEADER = "SID,SEASON,NAME,ISO_TIME,LAT,LON,TRACK_TYPE\n ,Year, , ,deg_n,deg_e, \n"

_EP_ROWS = (
    "EP182014,2014,ODILE,2014-09-10 00:00:00,15.0,-105.0,main\n"
    "EP182014,2014,ODILE,2014-09-18 00:00:00,28.0,-112.0,main\n"
    "EP182014,2014,ODILE,2014-09-18 06:00:00,28.5,-112.5,spur\n"
    "EP162014,2014,NORBERT,2014-09-02 00:00:00,18.0,-108.0,main\n"
    "EP162014,2014,NORBERT,2014-09-08 00:00:00,25.0,-115.0,main\n"
    "EP072014,2014,GENEVIEVE,2014-08-01 00:00:00,15.0,-140.0,main\n"
    "EP012015,2015,ANDRES,2015-05-28 00:00:00,14.0,-100.0,main\n"
    "EP012015,2015,ANDRES,2015-06-01 00:00:00,17.0,-107.0,main\n"
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
    assert set(storm_index["sid"]) == {
        "EP182014",
        "EP162014",
        "EP072014",
        "EP012015",
        "AL042014",
    }
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
        # LLUV inside ODILE's window, in a state its rain cone reaches → ciclonica.
        ("E3", "2014", "LLUV", "si", "", "Ciudad de México", "2014-09-15", "2014-09-16"),
        # INUND in a year with no matched storms → fluvial independiente.
        ("E4", "2013", "INUND", "si", "", "Tabasco", "2013-11-01", "2013-11-05"),
        # Named CT with no IBTrACS match and no dates → flagged, still ciclonica.
        ("E5", "2014", "CT", "si", "Huracán Fantasma", "Colima", "", ""),
        # INUND outside every storm window → mixes with ODILE in Sonora.
        ("E6", "2014", "INUND", "si", "", "Sonora", "2014-06-01", "2014-06-02"),
        # Out of the crosswalk universe: not climate / not ciclón-fluvial subtype.
        ("E7", "2014", "SIS", "no", "", "Oaxaca", "2014-01-01", "2014-01-01"),
        ("E8", "2014", "SEQ", "si", "", "Zacatecas", "2014-01-01", "2014-12-31"),
        # Date window overlapping DOLLY and NORBERT → footprint keeps only DOLLY.
        ("E9", "2014", "CT", "si", "", "Veracruz", "2014-08-22", "2014-09-01"),
        # CENAPRED typo → fuzzy name match to ODILE, flagged.
        (
            "E10",
            "2014",
            "CT",
            "si",
            "Ciclón Odyle",
            "Baja California Sur",
            "2014-09-14",
            "2014-09-17",
        ),
    ]
    return pd.DataFrame(filas, columns=columnas)


def _huellas() -> pd.DataFrame:
    filas = [
        # viento (m/s); v_thresh de prueba 25.7
        ("EP182014", "03", "viento", 45.0),  # ODILE BCS
        ("EP182014", "26", "viento", 24.0),  # ODILE Sonora, bajo v_thresh
        ("EP162014", "28", "viento", 28.0),  # NORBERT Tamaulipas
        ("AL042014", "19", "viento", 27.0),  # DOLLY Nuevo León: hazard sin evento
        ("EP012015", "12", "viento", 33.0),  # ANDRES Guerrero: fuera del panel
        # lluvia (mm); umbral de prueba 80
        ("EP182014", "03", "lluvia", 180.0),
        ("EP182014", "26", "lluvia", 120.0),
        ("EP182014", "09", "lluvia", 95.0),  # cono de ODILE alcanza CDMX
        ("AL042014", "30", "lluvia", 90.0),  # DOLLY toca Veracruz (desambiguación E9)
        ("EP162014", "28", "lluvia", 60.0),  # bajo umbral
    ]
    return pd.DataFrame(filas, columns=["sid", "cve_ent", "peril", "int_max"])


def test_build_crosswalk_end_to_end(storm_index):
    xwalk, match, resumen = build_crosswalk(_eventos(), storm_index, _CONFIG, _huellas())

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
    assert (xwalk["version_crosswalk"] == "v1-test").all()

    filas = {(r.anio, r.cve_ent): r for r in xwalk.itertuples()}
    # BCS (03): viento y cono de ODILE; fuzzy match del typo E10 queda flaggeado.
    assert filas[(2014, "03")].sids_viento == "EP182014"
    assert filas[(2014, "03")].sids_cono_lluvia == "EP182014"
    assert filas[(2014, "03")].familia_asignada == "ciclonica"
    assert "nombre_fuzzy" in filas[(2014, "03")].flag_revision
    # Tamaulipas (28): NORBERT supera v_thresh; su lluvia no supera el umbral.
    assert filas[(2014, "28")].sids_viento == "EP162014"
    assert filas[(2014, "28")].sids_cono_lluvia == ""
    assert filas[(2014, "28")].regla_aplicada == "ct_reportado"
    # CDMX (09): lluvia en el cono de ODILE y dentro de su ventana → ciclonica.
    assert filas[(2014, "09")].familia_asignada == "ciclonica"
    assert filas[(2014, "09")].regla_aplicada == "lluvia_en_cono_tormenta"
    assert filas[(2014, "09")].sids_cono_lluvia == "EP182014"
    # Sonora (26): CT + INUND fuera de ventana → mixta; viento bajo v_thresh.
    assert filas[(2014, "26")].familia_asignada == "mixta_flag"
    assert filas[(2014, "26")].sids_viento == ""
    assert filas[(2014, "26")].sids_cono_lluvia == "EP182014"
    # Tabasco 2013 (27): sin tormentas ese año → fluvial.
    assert filas[(2013, "27")].familia_asignada == "fluvial"
    assert filas[(2013, "27")].regla_aplicada == "fluvial_independiente"
    # Colima (06): CT sin match ni huella → verificación CAL-XWALK-01.
    assert filas[(2014, "06")].sids_viento == ""
    assert "ct_sin_sid" in filas[(2014, "06")].flag_revision
    assert "perdida_sin_tormenta_modelada" in filas[(2014, "06")].flag_revision
    # Veracruz (30): E9 desambiguado por huella → DOLLY en el cono.
    assert filas[(2014, "30")].sids_cono_lluvia == "AL042014"
    assert "candidatos_filtrados_huella" in filas[(2014, "30")].flag_revision
    # Nuevo León (19): afectado solo por hazard dentro del panel.
    assert filas[(2014, "19")].familia_asignada == ""
    assert filas[(2014, "19")].regla_aplicada == "afectado_solo_hazard"
    assert filas[(2014, "19")].flag_revision == "tormenta_sin_perdida"
    assert filas[(2014, "19")].sids_viento == "AL042014"
    # Guerrero (12) 2015: hazard posterior al panel CENAPRED.
    assert filas[(2015, "12")].flag_revision == "fuera_panel_cenapred"
    # Fuera de universo: no entran.
    assert (2014, "20") not in filas and (2014, "32") not in filas

    metodos = match.set_index("evento_id")["metodo_match"]
    assert metodos["E1"] == "nombre"
    assert metodos["E2"] == "fechas"
    assert metodos["E5"] == "sin_match"
    assert metodos["E9"] == "fechas"
    assert metodos["E10"] == "nombre"
    flags = match.set_index("evento_id")["flag_evento"]
    assert "candidatos_filtrados_huella" in flags["E9"]
    assert "candidatos_multiples" not in flags["E9"]
    assert "nombre_fuzzy" in flags["E10"]
    assert resumen["n_eventos_ct"] == 5
    assert resumen["umbral_lluvia_mm"] == 80.0


def test_build_crosswalk_requires_umbral(storm_index):
    config = {**_CONFIG, "crosswalk": {**_CONFIG["crosswalk"], "umbral_lluvia_mm": None}}
    with pytest.raises(ValueError, match="umbral_lluvia_mm"):
        build_crosswalk(_eventos(), storm_index, config, _huellas())
