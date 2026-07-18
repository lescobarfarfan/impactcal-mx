"""Investigación: outlier 2015 en Maíz dulce (CNSF agrícola), foco Sinaloa.

Lee los consolidados CNSF (emision.csv / siniestros.csv) del repo hermano
climateCCR, agrega por año x entidad para CULTIVO = 'Maíz dulce', imprime y
guarda estadísticas de verificación del salto 2015, y genera las figuras de
comportamiento histórico 2008-2024.

Uso: python analisis_maiz_dulce.py   (salidas junto al script; idempotente)
"""

import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

DATA_DIR = Path(
    "/Users/lescobarfarfan/Documents/projects/Thesis_MScQF/climateCCR/"
    "data/hazard_mx/datos_CNSF/consolidados/agricola_y_animales"
)
OUT = Path(__file__).resolve().parent

SUP_EM = "SUPERFICIE ASEGURADA\n(HECTÁREAS)"
SUP_SI = "SUPERFICIE SINIESTRADA\n(HECTÁREAS)"

# Paleta categórica validada (dataviz skill, superficie clara #fcfcfb)
COLORS = {
    "SINALOA": "#2a78d6",
    "SONORA": "#008300",
    "GUANAJUATO": "#e87ba4",
    "SAN LUIS POTOSI": "#eda100",
}
LABEL_DY = {"SINALOA": 0, "SONORA": 0, "GUANAJUATO": -10, "SAN LUIS POTOSI": 7}
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2dd"


def _ascii_upper(s: pd.Series) -> pd.Series:
    def fold(x: str) -> str:
        return (
            unicodedata.normalize("NFKD", str(x).strip()).encode("ascii", "ignore").decode().upper()
        )

    return s.map(fold)


def load(name: str) -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / f"{name}.csv", encoding="utf-8-sig", low_memory=False)
    df["ENTIDAD_N"] = _ascii_upper(df["ENTIDAD"])
    df["CULTIVO_N"] = _ascii_upper(df["CULTIVO"].fillna(""))
    return df


def yearly(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    md = df[df["CULTIVO_N"] == "MAIZ DULCE"]
    return md.groupby(["anio", "ENTIDAD_N"])[cols].sum().reset_index()


def robust_stats(series: pd.Series, year: int = 2015) -> str:
    rest = series.drop(index=year, errors="ignore").dropna()
    med, mad = rest.median(), (rest - rest.median()).abs().median()
    x = series.get(year, float("nan"))
    z = 0.6745 * (x - med) / mad if mad else float("inf")
    return (
        f"2015={x:,.0f} | mediana otros años={med:,.1f} | MAD={mad:,.1f} | "
        f"z-robusta={z:,.0f} | ratio 2015/mediana={x / med:,.0f}x"
    )


def style_ax(ax, title):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, fontsize=10, color=INK, loc="left")
    ax.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.axvspan(2014.5, 2015.5, color="#e34948", alpha=0.08, zorder=0)


def human(x, _pos=None):
    for div, suf in ((1e9, " mil M"), (1e6, " M"), (1e3, " k")):
        if abs(x) >= div:
            return f"{x / div:g}{suf}"
    return f"{x:g}"


def plot_panels(tab: pd.DataFrame, panels: list[tuple[str, str, bool]], fname: str, suptitle: str):
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), facecolor=SURFACE)
    years = range(int(tab["anio"].min()), int(tab["anio"].max()) + 1)
    for ax, (col, title, logscale) in zip(axes.flat, panels, strict=True):
        style_ax(ax, title)
        for ent, color in COLORS.items():
            s = tab[tab["ENTIDAD_N"] == ent].set_index("anio")[col].reindex(years)
            if s.fillna(0).eq(0).all():
                continue
            if logscale:
                s = s.where(s > 0)
            ax.plot(s.index, s.values, color=color, linewidth=2, marker="o", markersize=4)
            last = s.dropna()
            if len(last):
                ax.annotate(
                    ent.title(),
                    (last.index[-1], last.iloc[-1]),
                    textcoords="offset points",
                    xytext=(5, LABEL_DY[ent]),
                    fontsize=7,
                    color=color,
                )
        if logscale:
            ax.set_yscale("log")
            ax.set_title(title + "  (escala log)", fontsize=10, color=INK, loc="left")
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(human))
        ax.xaxis.set_major_locator(mtick.MaxNLocator(integer=True))
        ax.set_xlim(min(years) - 0.5, max(years) + 2.5)
    handles = [plt.Line2D([], [], color=c, linewidth=2, label=e.title()) for e, c in COLORS.items()]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8)
    fig.suptitle(suptitle, color=INK, fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    fig.savefig(OUT / fname, dpi=150)
    plt.close(fig)


def main() -> None:
    em, si = load("emision"), load("siniestros")

    cols_em = ["NÚMERO DE PÓLIZAS", SUP_EM, "PRIMA EMITIDA", "SUMA ASEGURADA"]
    cols_si = ["NÚMERO DE SINIESTROS", SUP_SI, "MONTO DEL SINIESTRO OCURRIDO", "MONTO PAGADO"]
    tab_em, tab_si = yearly(em, cols_em), yearly(si, cols_si)
    tab_em.to_csv(OUT / "emision_anual_maiz_dulce.csv", index=False)
    tab_si.to_csv(OUT / "siniestros_anual_maiz_dulce.csv", index=False)

    lines = ["# Resumen estadístico — Maíz dulce, CNSF agrícola 2008-2024", ""]
    sin_em = tab_em[tab_em["ENTIDAD_N"] == "SINALOA"].set_index("anio")
    sin_si = tab_si[tab_si["ENTIDAD_N"] == "SINALOA"].set_index("anio")
    lines += [
        "Sinaloa, superficie asegurada (ha):  " + robust_stats(sin_em[SUP_EM]),
        "Sinaloa, superficie siniestrada (ha): " + robust_stats(sin_si[SUP_SI]),
        "Sinaloa, prima emitida (MXN):         " + robust_stats(sin_em["PRIMA EMITIDA"]),
        "Sinaloa, monto pagado (MXN):          " + robust_stats(sin_si["MONTO PAGADO"]),
        "",
        "Valor implícito asegurado (suma asegurada / superficie, MXN/ha), Sinaloa:",
        (sin_em["SUMA ASEGURADA"] / sin_em[SUP_EM]).round(0).to_string(),
        "",
    ]

    # ¿El outlier es exclusivo de maíz dulce 2015, o hay más celdas imposibles en la base?
    big = em.groupby(["anio", "ENTIDAD_N", "CULTIVO_N"])[SUP_EM].sum().reset_index()
    big = big[big[SUP_EM] > 200_000].sort_values(SUP_EM, ascending=False)
    big.to_csv(OUT / "celdas_superficie_mayor_200k_ha.csv", index=False)
    lines += [
        "Celdas año x entidad x cultivo con superficie asegurada > 200,000 ha (toda la base):",
        big.to_string(index=False),
        "",
        "Causas de siniestro, Maíz dulce Sinaloa 2015 (superficie siniestrada en ha):",
        si.query("anio == 2015 and ENTIDAD_N == 'SINALOA' and CULTIVO_N == 'MAIZ DULCE'")
        .groupby("CAUSA DEL SINIESTRO")[[SUP_SI, "MONTO PAGADO"]]
        .sum()
        .to_string(),
    ]
    (OUT / "resumen_estadistico.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))

    plot_panels(
        tab_em,
        [
            (SUP_EM, "Superficie asegurada (ha)", True),
            ("NÚMERO DE PÓLIZAS", "Número de pólizas", False),
            ("PRIMA EMITIDA", "Prima emitida (MXN)", False),
            ("SUMA ASEGURADA", "Suma asegurada (MXN)", True),
        ],
        "fig_emision_maiz_dulce.png",
        "CNSF agrícola — Emisión, Maíz dulce por entidad (2008-2024)",
    )
    plot_panels(
        tab_si,
        [
            (SUP_SI, "Superficie siniestrada (ha)", True),
            ("NÚMERO DE SINIESTROS", "Número de siniestros", False),
            ("MONTO DEL SINIESTRO OCURRIDO", "Monto del siniestro ocurrido (MXN)", False),
            ("MONTO PAGADO", "Monto pagado (MXN)", False),
        ],
        "fig_siniestros_maiz_dulce.png",
        "CNSF agrícola — Siniestros, Maíz dulce por entidad (2008-2024)",
    )

    # Consistencia interna Sinaloa: MXN/ha implícito (emisión y siniestros), un solo eje
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=SURFACE)
    style_ax(ax, "Sinaloa, Maíz dulce — valor implícito por hectárea (MXN/ha, escala log)")
    for series, label, color in [
        (sin_em["SUMA ASEGURADA"] / sin_em[SUP_EM], "Suma asegurada / sup. asegurada", "#2a78d6"),
        (
            sin_si["MONTO DEL SINIESTRO OCURRIDO"] / sin_si[SUP_SI],
            "Monto ocurrido / sup. siniestrada",
            "#eb6834",
        ),
    ]:
        s = series.where(series > 0)
        ax.plot(s.index, s.values, color=color, linewidth=2, marker="o", markersize=4, label=label)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(human))
    ax.annotate(
        "2015: ~25 MXN/ha implícitos\n(≈1000x menos que lo normal)",
        (2015, 30),
        textcoords="offset points",
        xytext=(15, 10),
        fontsize=8,
        color=INK,
    )
    ax.legend(frameon=False, fontsize=8, loc="lower left", labelcolor=INK2)
    fig.tight_layout()
    fig.savefig(OUT / "fig_consistencia_mxn_por_ha.png", dpi=150)
    plt.close(fig)
    print(f"\nFiguras y tablas escritas en {OUT}")


if __name__ == "__main__":
    main()
