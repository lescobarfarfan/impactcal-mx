"""End-to-end test for the ruta B loss table (DC-CAL-TARGET-2)."""

import pandas as pd
import pytest

from impactcal.target.perdidas import build_perdidas, fuente_publicacion

_CONFIG = {"periodo": {"anio_inicial": 2000, "anio_final": 2023}}

_PANEL = pd.DataFrame(
    [
        # (entidad, anio, peril, n_eventos, danio_mdp, defunciones)
        ("Guerrero", 2023, "Ciclón tropical", 3, 100.0, 5.0),
        ("Guerrero", 2023, "Marejada", 1, 20.0, 0.0),
        ("Guerrero", 2023, "Daños por lluvia", 2, 30.0, 1.0),
        ("Guerrero", 2023, "Sequía", 1, 999.0, 0.0),  # fuera de alcance
        ("Tabasco", 2020, "Inundación", 1, 50.0, 2.0),
        ("Tabasco", 2024, "Ciclón tropical", 1, 77.0, 0.0),  # fuera del panel
        ("Tabasco", 1999, "Ciclón tropical", 1, 88.0, 0.0),  # fuera del panel
    ],
    columns=["entidad", "anio", "peril_canonico", "n_eventos", "danio_mdp", "defunciones"],
)

_XWALK = pd.DataFrame(
    [
        (2023, "12", "ciclonica", "", "v1.1-test"),
        (2020, "27", "fluvial", "tormenta_sin_perdida", "v1.1-test"),
    ],
    columns=["anio", "cve_ent", "familia_asignada", "flag_revision", "version_crosswalk"],
)


def test_build_perdidas_end_to_end():
    out = build_perdidas(_PANEL, _XWALK, _CONFIG)

    # ventana del panel respetada: 1999 y 2024 fuera
    assert set(out["anio"]) == {2020, 2023}
    # Sequía no entra
    assert out["monto_total_mxn_corr"].sum() == pytest.approx(200.0 * 1e6)

    gro = out[(out["anio"] == 2023) & (out["cve_ent"] == "12")].set_index("familia_peril")
    # ciclón + marejada se suman en una sola fila ciclónica
    assert gro.loc["ciclonica", "monto_total_mxn_corr"] == pytest.approx(120.0 * 1e6)
    assert gro.loc["fluvial", "monto_total_mxn_corr"] == pytest.approx(30.0 * 1e6)
    # la atribución del crosswalk viaja aparte de lo que reporta CENAPRED
    assert gro.loc["fluvial", "familia_xwalk"] == "ciclonica"
    assert gro.loc["ciclonica", "fuente_publicacion"] == "extenso_2023"

    tab = out[out["anio"] == 2020].iloc[0]
    assert tab["cve_ent"] == "27" and tab["familia_peril"] == "fluvial"
    assert tab["flag_revision"] == "tormenta_sin_perdida"
    assert tab["fuente_publicacion"] == "base_abierta_2000_2015" or tab["anio"] > 2015


def test_entidad_desconocida_falla_ruidosamente():
    panel = _PANEL.assign(entidad="Narnia")
    with pytest.raises(ValueError, match="clave INEGI"):
        build_perdidas(panel, _XWALK, _CONFIG)


def test_fuente_publicacion():
    assert fuente_publicacion(2015) == "base_abierta_2000_2015"
    assert fuente_publicacion(2016) == "extenso_2016"
    assert fuente_publicacion(2024) == "resumen_2024"
