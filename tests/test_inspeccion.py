"""Tests de impactcal.inspeccion sobre un panel sintético con errores plantados."""

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from impactcal.inspeccion import inspect_dataset, main, resolve_column  # noqa: E402


@pytest.fixture()
def datos() -> pd.DataFrame:
    rows = []
    for anio in range(2010, 2022):
        for ent in ("A", "B", "C"):
            for i, cult in enumerate(("Maíz dulce", "Frijol")):
                base = 100.0 * (1 + i) * (ord(ent) - 64)
                sup = base + anio % 5
                suma = sup * (15_000.0 + (anio % 7) * 10)
                monto = float("nan") if anio in (2012, 2013) else sup * 900.0
                rows.append([anio, ent, cult, sup, suma, monto])
    df = pd.DataFrame(rows, columns=["anio", "entidad", "cultivo", "superficie", "suma", "monto"])
    err = (df["anio"] == 2015) & (df["entidad"] == "A") & (df["cultivo"] == "Maíz dulce")
    df.loc[err, "superficie"] *= 1000  # error de magnitud tipo Maíz dulce Sinaloa 2015
    df.loc[df.index[:3], "cultivo"] = "MAIZ DULCE "  # etiqueta casi duplicada
    return df


def test_detecta_errores_plantados(datos: pd.DataFrame, tmp_path) -> None:
    tabla = inspect_dataset(
        datos,
        tmp_path / "out",
        time_col="anio",
        group_cols=("entidad", "cultivo"),
        ratios=(("suma", "superficie"),),
        source="sintetico",
    )

    celda = "entidad=A | cultivo=Maíz dulce | anio=2015"
    serie = tabla[(tabla["chequeo"] == "atipico_serie") & (tabla["columna"] == "superficie")]
    en_celda = serie["donde"].str.contains(celda, regex=False)
    assert en_celda.any()
    assert (serie.loc[en_celda, "triaje"] == "error_probable").all()
    razon = tabla[tabla["chequeo"] == "razon_atipica"]
    assert razon["donde"].str.contains(celda, regex=False).any()
    assert (tabla["chequeo"] == "categorias_similares").any()
    assert (
        tabla.loc[tabla["chequeo"] == "categorias_similares", "triaje"]
        == "inconsistencia_estructural"
    ).all()
    assert (tabla["chequeo"] == "faltantes_sistematicos").any()

    assert (tmp_path / "out" / "hallazgos.csv").exists()
    assert (tmp_path / "out" / "resumen.md").exists()
    assert len(list((tmp_path / "out" / "figuras").glob("*.png"))) >= 4


def test_cli(datos: pd.DataFrame, tmp_path) -> None:
    csv = tmp_path / "datos.csv"
    datos.to_csv(csv, index=False)
    main(
        [
            str(csv),
            "--tiempo",
            "anio",
            "--grupo",
            "entidad",
            "cultivo",
            "--razon",
            "suma",
            "superficie",
            "--salida",
            str(tmp_path / "cli"),
        ]
    )
    assert (tmp_path / "cli" / "hallazgos.csv").exists()
    assert (tmp_path / "cli" / "resumen.md").exists()


def test_resolve_column_laxo() -> None:
    df = pd.DataFrame(columns=["SUPERFICIE ASEGURADA\n(HECTÁREAS)"])
    assert (
        resolve_column(df, "superficie asegurada (hectareas)")
        == "SUPERFICIE ASEGURADA\n(HECTÁREAS)"
    )
    with pytest.raises(ValueError):
        resolve_column(df, "no existe")
