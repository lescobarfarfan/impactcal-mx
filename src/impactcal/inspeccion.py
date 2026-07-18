"""Inspección genérica de calidad de datos: atípicos, consistencia y figuras QA.

Agnóstica a la fuente: recibe cualquier tabla (CSV/Parquet), detecta tipos de
columna y escribe un folder con ``hallazgos.csv``, ``resumen.md`` y
``figuras/*.png``. Los chequeos robustos (mediana/MAD) por grupo x tiempo y las
razones derivadas (numerador/denominador) son los que detectan errores de
magnitud tipo "Maíz dulce Sinaloa 2015" (error x1000 en superficie).

Cada hallazgo lleva una etiqueta de triaje (``error_probable`` /
``atipico_a_revisar`` / ``inconsistencia_estructural``) que indica el paso
siguiente: corregir, revisar con criterio de dominio, o arreglar en pipeline.

Uso (salidas no versionadas, reproducibles: results/inspeccion/<fuente>/):
    python -m impactcal.inspeccion datos.csv --tiempo anio \\
        --grupo ENTIDAD CULTIVO \\
        --razon "SUMA ASEGURADA" "SUPERFICIE ASEGURADA (HECTÁREAS)" \\
        --salida results/inspeccion/cnsf_emision

Los nombres de columna se aceptan con espacios/acentos/mayúsculas laxos (los
consolidados CNSF traen saltos de línea dentro de los encabezados).
"""

from __future__ import annotations

import argparse
import re
import shlex
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2dd"
SERIES, FLAG = "#2a78d6", "#d03b3b"
SEQ_STEPS = ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#0d366b"]
MIN_PERIODS = 5

COLUMNAS_HALLAZGOS = ["chequeo", "columna", "donde", "valor", "referencia", "z_robusta", "detalle"]


def _fold(x: object) -> str:
    s = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().casefold()


def resolve_column(df: pd.DataFrame, name: str) -> str:
    """Match a column by exact name, else by whitespace/accent/case-folded name."""
    if name in df.columns:
        return name
    matches = [c for c in df.columns if _fold(c) == _fold(name)]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"columna '{name}' no encontrada; disponibles: {list(df.columns)}")


def robust_z(x: pd.Series, rel_floor: float = 0.0) -> pd.Series:
    """Robust z-score: (x - median) / (MAD/0.6745), IQR fallback when MAD is 0.

    ``rel_floor`` bounds the scale from below at that fraction of |median|, so
    near-constant series don't turn trivial deviations into astronomical z.
    """
    x = pd.to_numeric(x, errors="coerce")
    med = x.median()
    mad = (x - med).abs().median()
    scale = mad / 0.6745 if mad else (x.quantile(0.75) - x.quantile(0.25)) / 1.349
    if rel_floor and not np.isnan(med):
        scale = max(scale if not np.isnan(scale) else 0.0, rel_floor * abs(med))
    if not scale or np.isnan(scale):
        return pd.Series(np.nan, index=x.index)
    return (x - med) / scale


def human(x: float, _pos: int | None = None) -> str:
    for div, suf in ((1e9, " mil M"), (1e6, " M"), (1e3, " k")):
        if abs(x) >= div:
            return f"{x / div:g}{suf}"
    return f"{x:g}"


def _style_ax(ax, title: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, fontsize=9, color=INK, loc="left")
    ax.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=7)


def _save(fig, fig_dir: Path, name: str, figures: list[str]) -> None:
    fig.savefig(fig_dir / name, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(fig)
    figures.append(name)


def _where(row: pd.Series, group_cols: list[str], time_col: str | None) -> str:
    parts = [f"{g}={row[g]}" for g in group_cols]
    if time_col is not None:
        parts.append(f"{time_col}={row[time_col]}")
    return " | ".join(parts) if parts else f"fila {row.name}"


def _add(
    findings: list[dict],
    chequeo: str,
    columna: str,
    donde: str,
    valor=None,
    referencia=None,
    z=None,
    detalle: str = "",
) -> None:
    findings.append(
        {
            "chequeo": chequeo,
            "columna": columna,
            "donde": donde,
            "valor": valor,
            "referencia": referencia,
            "z_robusta": z,
            "detalle": detalle,
        }
    )


# ---------------------------------------------------------------- chequeos


def _check_basics(df: pd.DataFrame, findings: list[dict]) -> None:
    n_dup = int(df.duplicated().sum())
    if n_dup:
        _add(
            findings,
            "duplicados",
            "(todas)",
            "filas completas duplicadas",
            valor=n_dup,
            detalle="filas idénticas en todas las columnas; posible doble carga",
        )
    for col in df.columns:
        if df[col].nunique(dropna=False) == 1:
            _add(
                findings,
                "constante",
                col,
                "toda la tabla",
                valor=df[col].iloc[0],
                detalle="columna con un solo valor; no aporta información",
            )


def _check_missing(df: pd.DataFrame, time_col: str | None, findings: list[dict]) -> None:
    frac = df.isna().mean()
    for col in frac[frac > 0.2].index:
        _add(
            findings,
            "faltantes",
            col,
            "toda la tabla",
            valor=round(float(frac[col]), 3),
            detalle=f"{frac[col]:.0%} de valores faltantes",
        )
    if time_col is None:
        return
    for col in df.columns[df.isna().any()]:
        if col == time_col:
            continue
        by_t = df[col].isna().groupby(df[time_col]).mean()
        if by_t.max() >= 0.5 and by_t.min() <= 0.05:
            bad = [str(t) for t in by_t[by_t >= 0.5].index]
            _add(
                findings,
                "faltantes_sistematicos",
                col,
                f"{time_col} en {{{', '.join(bad[:8])}}}",
                valor=round(float(by_t.max()), 3),
                detalle="faltantes concentrados en periodos específicos (bloque sistemático); "
                "sesga inferencia si se trata como aleatorio",
            )


def _check_categorical(df: pd.DataFrame, cat_cols: list[str], findings: list[dict]) -> None:
    for col in cat_cols:
        counts = df[col].value_counts(dropna=True)
        if counts.empty:
            continue
        variants: dict[str, list] = defaultdict(list)
        for val in counts.index:
            variants[_fold(val)].append(val)
        for group in list(variants.values()):
            if len(group) > 1:
                detail = ", ".join(f"'{v}' ({counts[v]})" for v in group)
                _add(
                    findings,
                    "categorias_similares",
                    col,
                    "etiquetas que difieren solo en " "mayúsculas/acentos/espacios",
                    valor=len(group),
                    detalle=detail,
                )
        rare = counts[counts == 1]
        if len(rare) and len(counts) > 10:
            ejemplos = ", ".join(map(str, rare.index[:8]))
            _add(
                findings,
                "categoria_rara",
                col,
                "toda la tabla",
                valor=len(rare),
                detalle=f"categorías con una sola fila (posibles errores de captura): {ejemplos}",
            )


def _check_numeric_global(
    df: pd.DataFrame,
    num_cols: list[str],
    group_cols: list[str],
    time_col: str | None,
    threshold: float,
    findings: list[dict],
) -> None:
    for col in num_cols:
        x = pd.to_numeric(df[col], errors="coerce").dropna()
        zero_note = ""
        if len(x) and (x == 0).mean() > 0.5 and (x != 0).sum() >= 20:
            x = x[x != 0]
            zero_note = f"; evaluado sobre {len(x)} valores ≠ 0 (columna dominada por ceros)"
        if len(x) < 20:
            continue
        log_scale = (x > 0).mean() > 0.95 and x.skew() > 3
        z = robust_z(np.log10(x[x > 0])) if log_scale else robust_z(x)
        flagged = z[z.abs() > threshold]
        if flagged.empty:
            continue
        worst = flagged.abs().idxmax()
        _add(
            findings,
            "atipico_global",
            col,
            _where(df.loc[worst], group_cols, time_col),
            valor=float(df.loc[worst, col]),
            referencia=float(x.median()),
            z=round(float(z[worst]), 1),
            detalle=f"{len(flagged)} valores con |z|>{threshold:g}"
            + (" (escala log10, distribución sesgada)" if log_scale else "")
            + zero_note,
        )


def _check_panel(
    agg: pd.DataFrame,
    num_cols: list[str],
    group_cols: list[str],
    time_col: str,
    threshold: float,
    findings: list[dict],
) -> list[tuple[float, tuple, str]]:
    """Robust z per group across time on the aggregated panel; the Maíz-dulce detector."""
    flagged_cells: list[tuple[float, tuple, str]] = []
    for col in num_cols:
        if group_cols:
            g = agg.groupby(group_cols, dropna=False, observed=True)[col]
            z = g.transform(lambda s: robust_z(s, rel_floor=0.01))
            n, med = g.transform("count"), g.transform("median")
        else:
            z, med = robust_z(agg[col], rel_floor=0.01), agg[col].median()
            n = pd.Series(agg[col].count(), index=agg.index)
        z = z.where(n >= MIN_PERIODS)
        for idx in z[z.abs() > threshold].index:
            row = agg.loc[idx]
            ref = float(med if np.isscalar(med) else med.loc[idx])
            _add(
                findings,
                "atipico_serie",
                col,
                _where(row, group_cols, time_col),
                valor=float(row[col]),
                referencia=ref,
                z=round(float(z.loc[idx]), 1),
                detalle=(
                    f"valor {row[col] / ref:,.0f}x la mediana del grupo"
                    if ref
                    else "grupo con mediana 0"
                ),
            )
            flagged_cells.append((abs(float(z.loc[idx])), tuple(row[g] for g in group_cols), col))
    return flagged_cells


def _safe_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    return (num / den).replace([np.inf, -np.inf], np.nan).where(lambda s: s > 0)


def _check_ratios(
    agg: pd.DataFrame,
    ratios: list[tuple[str, str]],
    group_cols: list[str],
    time_col: str,
    threshold: float,
    findings: list[dict],
) -> dict[int, pd.Series]:
    """Global robust z on log10(num/den) per aggregated cell; unit errors are multiplicative."""
    flags: dict[int, pd.Series] = {}
    for i, (num, den) in enumerate(ratios):
        r = _safe_ratio(agg[num], agg[den])
        rlog = np.log10(r)
        z_glob = robust_z(rlog.dropna()).reindex(agg.index)
        if group_cols:
            gb = rlog.groupby([agg[g] for g in group_cols], dropna=False)
            z_grp = gb.transform(robust_z).where(gb.transform("count") >= MIN_PERIODS)
        else:
            z_grp = pd.Series(np.nan, index=agg.index)
        z = z_glob.where(z_glob.abs().fillna(0) >= z_grp.abs().fillna(0), z_grp)
        flags[i] = z
        undef = int(((agg[den] <= 0) & (agg[num] > 0)).sum())
        if undef:
            _add(
                findings,
                "razon_indefinida",
                f"{num} / {den}",
                "celdas con denominador 0 y numerador > 0",
                valor=undef,
                detalle="montos sin base física (p. ej. filas pecuarias sin superficie); "
                "estructura distinta o denominador mal capturado",
            )
        for idx in z[z.abs() > threshold].index:
            row = agg.loc[idx]
            _add(
                findings,
                "razon_atipica",
                f"{num} / {den}",
                _where(row, group_cols, time_col),
                valor=float(r.loc[idx]),
                referencia=float(r.median()),
                z=round(float(z.loc[idx]), 1),
                detalle=f"razón {np.log10(r.loc[idx] / r.median()):+.1f} órdenes de magnitud "
                "respecto a la mediana global"
                + (
                    " (detectada contra la historia de su propio grupo)"
                    if abs(z_grp.get(idx, np.nan)) > abs(z_glob.get(idx, 0) or 0)
                    else ""
                )
                + "; sugiere error de unidades",
            )
    return flags


def _check_coverage(
    df: pd.DataFrame, time_col: str, threshold: float, findings: list[dict]
) -> None:
    rows = df.groupby(df[time_col].dropna()).size()
    z = robust_z(rows)
    for t in z[z.abs() > threshold].index:
        _add(
            findings,
            "cobertura_periodo",
            "(filas por periodo)",
            f"{time_col}={t}",
            valor=int(rows[t]),
            referencia=float(rows.median()),
            z=round(float(z[t]), 1),
            detalle="conteo de filas anómalo en el periodo; posible carga incompleta o doble",
        )


# ----------------------------------------------------------------- figuras


def _fig_missing(df: pd.DataFrame, time_col: str | None, fig_dir: Path, figures: list[str]) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    if not df.isna().values.any():
        return
    view = df.sort_values(time_col) if time_col else df
    step = max(1, len(view) // 4000)
    m = view.isna().iloc[::step]
    fig, ax = plt.subplots(figsize=(max(7, 0.4 * df.shape[1]), 5), facecolor=SURFACE)
    ax.imshow(
        m.to_numpy(),
        aspect="auto",
        interpolation="nearest",
        cmap=ListedColormap([SEQ_STEPS[2], SURFACE]),
    )
    ax.set_title(
        "Matriz de faltantes (blanco = faltante"
        + (f"; filas ordenadas por {time_col})" if time_col else ")"),
        fontsize=9,
        color=INK,
        loc="left",
    )
    ax.set_xticks(range(df.shape[1]))
    ax.set_xticklabels(
        [re.sub(r"\s+", " ", str(c))[:25] for c in df.columns], rotation=90, fontsize=6, color=INK2
    )
    ax.set_yticks([])
    ax.set_ylabel("filas", color=INK2, fontsize=8)
    _save(fig, fig_dir, "01_faltantes_matriz.png", figures)

    frac = df.isna().mean()
    frac = frac[frac > 0].sort_values()
    fig, ax = plt.subplots(figsize=(7, max(2, 0.3 * len(frac))), facecolor=SURFACE)
    _style_ax(ax, "Porcentaje de faltantes por columna")
    ax.barh(
        [re.sub(r"\s+", " ", str(c))[:40] for c in frac.index],
        frac * 100,
        color=SEQ_STEPS[2],
        height=0.6,
    )
    ax.set_xlabel("% faltante", color=INK2, fontsize=8)
    _save(fig, fig_dir, "02_faltantes_por_columna.png", figures)


def _fig_categorical(
    df: pd.DataFrame, cat_cols: list[str], group_cols: list[str], fig_dir: Path, figures: list[str]
) -> None:
    import matplotlib.pyplot as plt

    ordered = [c for c in group_cols if c in cat_cols]
    ordered += sorted((c for c in cat_cols if c not in ordered), key=lambda c: df[c].nunique())
    chosen = [c for c in ordered if 1 < df[c].nunique() <= 5000][:4]
    for i, col in enumerate(chosen):
        counts = df[col].value_counts()
        top = counts.head(20)[::-1]
        fig, ax = plt.subplots(figsize=(7, max(2.5, 0.28 * len(top))), facecolor=SURFACE)
        _style_ax(
            ax,
            f"{col} — frecuencia de las 20 categorías más comunes "
            f"({len(counts)} categorías en total)",
        )
        ax.barh([str(v)[:40] for v in top.index], top.values, color=SEQ_STEPS[2], height=0.6)
        if len(top) > 1 and top.max() / max(top.min(), 1) > 100:
            ax.set_xscale("log")
        ax.set_xlabel("filas", color=INK2, fontsize=8)
        _save(fig, fig_dir, f"03_categorias_{i}_{_fold(col).replace(' ', '_')[:30]}.png", figures)


def _fig_ecdf(
    df: pd.DataFrame, num_cols: list[str], threshold: float, fig_dir: Path, figures: list[str]
) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick

    cols = [c for c in num_cols if (pd.to_numeric(df[c], errors="coerce") > 0).sum() >= 20][:12]
    if not cols:
        return
    ncols = min(4, len(cols))
    nrows = -(-len(cols) // ncols)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(3.2 * ncols, 2.6 * nrows), facecolor=SURFACE, squeeze=False
    )
    for ax in axes.flat[len(cols) :]:
        ax.axis("off")
    for ax, col in zip(axes.flat, cols, strict=False):
        x = pd.to_numeric(df[col], errors="coerce")
        x = np.sort(x[x > 0].to_numpy())
        y = np.arange(1, len(x) + 1) / len(x)
        z = robust_z(pd.Series(np.log10(x)))
        bad = z.abs().to_numpy() > threshold
        _style_ax(ax, re.sub(r"\s+", " ", str(col))[:38])
        ax.plot(x, y, color=SERIES, linewidth=1.5)
        if bad.any():
            ax.scatter(x[bad], y[bad], color=FLAG, s=12, zorder=3)
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(human))
    fig.suptitle(
        f"ECDF en escala log — valores positivos; rojo: |z robusta|>{threshold:g} "
        "en log10 (colas separadas ⇒ posible error de magnitud)",
        color=INK,
        fontsize=10,
        x=0.01,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _save(fig, fig_dir, "04_ecdf_numericas.png", figures)


def _fig_coverage(
    df: pd.DataFrame,
    group_cols: list[str],
    time_col: str,
    fig_dir: Path,
    figures: list[str],
    notes: list[str],
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    if not group_cols:
        return
    glabel, gname = df[group_cols[0]].astype(str), str(group_cols[0])
    if len(group_cols) > 1 and df.groupby(group_cols).ngroups <= 45:
        glabel = df[group_cols].astype(str).agg(" | ".join, axis=1)
        gname = " x ".join(map(str, group_cols))
    counts = pd.crosstab(glabel, df[time_col])
    if counts.shape[1] > 150:
        notes.append(
            f"figura de cobertura omitida: {counts.shape[1]} periodos en {time_col} "
            "(demasiados para un heatmap legible)."
        )
        return
    if len(counts) > 45:
        keep = counts.sum(axis=1).nlargest(45).index
        notes.append(
            f"figura de cobertura: se muestran 45 de {len(counts)} grupos "
            f"(los de más filas), agrupados por {group_cols[0]}."
        )
        counts = counts.loc[keep]
    counts = counts.sort_index()
    cmap = LinearSegmentedColormap.from_list("azul", SEQ_STEPS).with_extremes(bad=SURFACE)
    fig, ax = plt.subplots(
        figsize=(max(7, 0.3 * counts.shape[1]), max(3, 0.22 * counts.shape[0])), facecolor=SURFACE
    )
    im = ax.imshow(
        np.where(counts.to_numpy() == 0, np.nan, counts.to_numpy()),
        aspect="auto",
        interpolation="nearest",
        cmap=cmap,
    )
    ax.set_title(
        f"Cobertura: filas por {gname} y {time_col} (blanco = sin filas)",
        fontsize=9,
        color=INK,
        loc="left",
    )
    ax.set_xticks(range(counts.shape[1]))
    ax.set_xticklabels([str(c) for c in counts.columns], rotation=90, fontsize=6, color=INK2)
    ax.set_yticks(range(counts.shape[0]))
    ax.set_yticklabels([str(v)[:35] for v in counts.index], fontsize=6, color=INK2)
    fig.colorbar(im, ax=ax, shrink=0.7).set_label("filas", color=INK2, fontsize=8)
    _save(fig, fig_dir, "05_cobertura.png", figures)


def _fig_series(
    agg: pd.DataFrame,
    cells: list[tuple[float, tuple, str]],
    group_cols: list[str],
    time_col: str,
    threshold: float,
    fig_dir: Path,
    figures: list[str],
) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick

    worst: dict[tuple, float] = {}
    for zabs, gkey, col in cells:
        worst[(gkey, col)] = max(zabs, worst.get((gkey, col), 0.0))
    top = sorted(worst, key=worst.get, reverse=True)[:12]
    if not top:
        return
    ncols = min(3, len(top))
    nrows = -(-len(top) // ncols)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(4 * ncols, 2.6 * nrows), facecolor=SURFACE, squeeze=False
    )
    for ax in axes.flat[len(top) :]:
        ax.axis("off")
    for ax, (gkey, col) in zip(axes.flat, top, strict=False):
        sub = agg
        for g, v in zip(group_cols, gkey, strict=True):
            sub = sub[sub[g].eq(v) | (sub[g].isna() & pd.isna(v))]
        sub = sub.sort_values(time_col)
        z = robust_z(sub[col], rel_floor=0.01)
        bad = z.abs() > threshold
        label = " | ".join(map(str, gkey)) if gkey else "(toda la tabla)"
        col_name = re.sub(r"\s+", " ", str(col))[:45]
        _style_ax(ax, f"{label[:45]}\n{col_name}")
        ax.title.set_fontsize(8)
        ax.plot(sub[time_col], sub[col], color=SERIES, linewidth=1.8, marker="o", markersize=3)
        ax.scatter(sub.loc[bad, time_col], sub.loc[bad, col], color=FLAG, s=28, zorder=3)
        y = sub[col].dropna()
        if (y > 0).all() and len(y) and y.max() / max(y.median(), 1e-12) > 50:
            ax.set_yscale("log")
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(human))
        ax.xaxis.set_major_locator(mtick.MaxNLocator(5, integer=True))
    fig.suptitle(
        f"Series por grupo con celdas atípicas (rojo: |z robusta|>{threshold:g} "
        "dentro del grupo)",
        color=INK,
        fontsize=10,
        x=0.01,
        ha="left",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, fig_dir, "06_series_atipicas.png", figures)


def _fig_ratios(
    agg: pd.DataFrame,
    ratios: list[tuple[str, str]],
    zflags: dict[int, pd.Series],
    time_col: str,
    threshold: float,
    fig_dir: Path,
    figures: list[str],
) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick

    for i, (num, den) in enumerate(ratios[:4]):
        r = _safe_ratio(agg[num], agg[den])
        if r.dropna().empty:
            continue
        z = zflags[i]
        bad = z.abs() > threshold
        fig, ax = plt.subplots(figsize=(8, 4), facecolor=SURFACE)
        nnum = re.sub(r"\s+", " ", str(num))
        nden = re.sub(r"\s+", " ", str(den))
        _style_ax(ax, f"Razón {nnum} / {nden} por celda grupo x {time_col} (escala log)")
        ax.scatter(
            agg.loc[r.notna() & ~bad, time_col],
            r[r.notna() & ~bad],
            color=INK2,
            s=9,
            alpha=0.35,
            linewidths=0,
        )
        ax.scatter(
            agg.loc[bad, time_col],
            r[bad],
            color=FLAG,
            s=26,
            zorder=3,
            label=f"|z robusta|>{threshold:g} en log10",
        )
        ax.axhline(r.median(), color=INK2, linewidth=1, linestyle="--")
        ax.set_yscale("log")
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(human))
        ax.legend(frameon=False, fontsize=8, labelcolor=INK2)
        _save(fig, fig_dir, f"07_razon_{i}.png", figures)


# ------------------------------------------------------------------ triaje

ESTRUCTURALES = {
    "duplicados",
    "constante",
    "categorias_similares",
    "categoria_rara",
    "faltantes",
    "faltantes_sistematicos",
    "cobertura_periodo",
    "razon_indefinida",
}

TRIAJE_LEYENDA = [
    "`error_probable`: firma de error de captura/unidades (razón ≥2 órdenes de magnitud fuera, "
    "salto ≥1000x la mediana del grupo, o celda marcada también por razón atípica).",
    "`atipico_a_revisar`: valor extremo que puede ser un evento real (p. ej. huracán) o un "
    "error; requiere revisión de dominio antes de corregir o excluir.",
    "`inconsistencia_estructural`: defecto de estructura o captura (duplicados, etiquetas casi "
    "duplicadas, faltantes sistemáticos, cobertura anómala); se corrige en el pipeline, no "
    "celda por celda.",
]


def _triage(tabla: pd.DataFrame) -> pd.Series:
    """Etiqueta cada hallazgo según el paso siguiente que amerita (reglas deterministas)."""
    celdas_razon = set(tabla.loc[tabla["chequeo"] == "razon_atipica", "donde"])

    def rule(row: pd.Series) -> str:
        if row["chequeo"] in ESTRUCTURALES:
            return "inconsistencia_estructural"
        val, ref = row["valor"], row["referencia"]
        decades = abs(float(np.log10(abs(val / ref)))) if val and ref else 0.0
        if row["chequeo"] == "razon_atipica":
            return "error_probable" if decades >= 2 else "atipico_a_revisar"
        if row["chequeo"] == "atipico_serie" and (row["donde"] in celdas_razon or decades >= 3):
            return "error_probable"
        return "atipico_a_revisar"

    if tabla.empty:
        return pd.Series(dtype=object)
    return tabla.apply(rule, axis=1)


# ------------------------------------------------------------------ salida


def _md_table(df: pd.DataFrame) -> str:
    def fmt(v: object) -> str:
        if isinstance(v, float):
            return human(v) if abs(v) >= 1000 else f"{v:g}"
        return re.sub(r"\s+", " ", str(v))[:60]

    head = "| " + " | ".join(map(fmt, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    rows = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *rows])


def _write_summary(
    out_dir: Path,
    source: str,
    df: pd.DataFrame,
    findings: pd.DataFrame,
    figures: list[str],
    notes: list[str],
    threshold: float,
    command: str = "",
) -> None:
    tipos = pd.DataFrame(
        {
            "columna": df.columns,
            "dtype": [str(t) for t in df.dtypes],
            "% faltante": (df.isna().mean() * 100).round(1).values,
            "únicos": [df[c].nunique(dropna=False) for c in df.columns],
        }
    )
    lines = [
        f"# Inspección de datos — {source}",
        "",
        f"Fecha: {date.today().isoformat()} · Filas: {len(df):,} · Columnas: {df.shape[1]} · "
        f"Umbral |z robusta| (mediana/MAD): {threshold:g}",
        *(["", f"Reproducir: `{command}`"] if command else []),
        "",
        "## Columnas",
        "",
        _md_table(tipos),
        "",
        "## Hallazgos",
        "",
    ]
    if findings.empty:
        lines.append("Sin hallazgos por encima del umbral.")
    else:
        conteo = (
            findings.groupby(["triaje", "chequeo"])
            .size()
            .reset_index(name="n")
            .sort_values(["triaje", "n"], ascending=[True, False])
        )
        lines += [
            _md_table(conteo),
            "",
            *[f"- {leyenda}" for leyenda in TRIAJE_LEYENDA],
            "",
            f"Top 20 por |z| (de {len(findings)}; " "tabla completa en `hallazgos.csv`):",
            "",
            _md_table(findings.head(20)),
        ]
    lines += ["", "## Figuras", ""] + [f"- `figuras/{f}`" for f in figures]
    if notes:
        lines += ["", "## Notas", ""] + [f"- {n}" for n in notes]
    (out_dir / "resumen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------- API


def inspect_dataset(
    df: pd.DataFrame,
    out_dir: Path | str,
    *,
    time_col: str | None = None,
    group_cols: tuple[str, ...] = (),
    ratios: tuple[tuple[str, str], ...] = (),
    threshold: float = 5.0,
    source: str = "datos",
    profile: bool = False,
    command: str = "",
) -> pd.DataFrame:
    """Run all QA checks on ``df`` and write hallazgos.csv, resumen.md and figuras/.

    Returns the findings table (one row per flag plus a ``triaje`` label:
    error_probable / atipico_a_revisar / inconsistencia_estructural), sorted by
    |robust z|. ``command`` is recorded in resumen.md for reproducibility.
    """
    out_dir = Path(out_dir)
    fig_dir = out_dir / "figuras"
    fig_dir.mkdir(parents=True, exist_ok=True)

    df = df.copy()
    if time_col is not None:
        time_col = resolve_column(df, time_col)
        if not pd.api.types.is_numeric_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    group_cols = [resolve_column(df, g) for g in group_cols]
    ratios = [(resolve_column(df, n), resolve_column(df, d)) for n, d in ratios]

    num_cols = [c for c in df.select_dtypes("number").columns if c != time_col]
    cat_cols = [c for c in df.select_dtypes(["object", "category", "string", "bool"]).columns]

    findings: list[dict] = []
    notes: list[str] = []
    figures: list[str] = []

    _check_basics(df, findings)
    _check_missing(df, time_col, findings)
    _check_categorical(df, cat_cols, findings)
    _check_numeric_global(df, num_cols, group_cols, time_col, threshold, findings)
    _fig_missing(df, time_col, fig_dir, figures)
    _fig_categorical(df, cat_cols, group_cols, fig_dir, figures)
    _fig_ecdf(df, num_cols, threshold, fig_dir, figures)

    if time_col is not None:
        _check_coverage(df, time_col, threshold, findings)
        _fig_coverage(df, group_cols, time_col, fig_dir, figures, notes)
        keys = group_cols + [time_col]
        agg = (
            df.dropna(subset=[time_col])
            .groupby(keys, dropna=False, observed=True)[num_cols]
            .sum(min_count=1)
            .reset_index()
        )
        cells = _check_panel(agg, num_cols, group_cols, time_col, threshold, findings)
        _fig_series(agg, cells, group_cols, time_col, threshold, fig_dir, figures)
        if ratios:
            zflags = _check_ratios(agg, ratios, group_cols, time_col, threshold, findings)
            _fig_ratios(agg, ratios, zflags, time_col, threshold, fig_dir, figures)
    elif ratios:
        notes.append("razones ignoradas: requieren --tiempo para agregarse por celda.")

    if profile:
        try:
            from ydata_profiling import ProfileReport

            ProfileReport(df, title=f"Perfil — {source}", minimal=len(df) > 50_000).to_file(
                out_dir / "perfil.html"
            )
        except ImportError:
            notes.append(
                "ydata-profiling no instalado; perfil.html omitido "
                "(pip install ydata-profiling)."
            )

    tabla = pd.DataFrame(findings, columns=COLUMNAS_HALLAZGOS)
    tabla.insert(1, "triaje", _triage(tabla))
    tabla = tabla.sort_values(
        "z_robusta",
        key=lambda s: pd.to_numeric(s, errors="coerce").abs(),
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)
    tabla.to_csv(out_dir / "hallazgos.csv", index=False)
    _write_summary(out_dir, source, df, tabla, figures, notes, threshold, command)
    return tabla


def load_table(path: Path | str) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    try:
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1", low_memory=False)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m impactcal.inspeccion",
        description="Inspección de calidad de datos: atípicos robustos, consistencia y figuras.",
    )
    parser.add_argument("archivo", help="CSV o Parquet a inspeccionar")
    parser.add_argument("--tiempo", help="columna temporal (año o fecha)")
    parser.add_argument(
        "--grupo", nargs="*", default=[], help="columnas de agrupación (p. ej. ENTIDAD CULTIVO)"
    )
    parser.add_argument(
        "--razon",
        nargs=2,
        action="append",
        default=[],
        metavar=("NUMERADOR", "DENOMINADOR"),
        help="razón derivada a vigilar (repetible); detecta errores de unidades",
    )
    parser.add_argument("--salida", help="folder de salida (default: ./inspeccion_<archivo>)")
    parser.add_argument(
        "--umbral", type=float, default=5.0, help="umbral de |z robusta| para marcar (default 5)"
    )
    parser.add_argument(
        "--perfil",
        action="store_true",
        help="además genera perfil.html con ydata-profiling si está instalado",
    )
    args = parser.parse_args(argv)

    df = load_table(args.archivo)
    out = Path(args.salida) if args.salida else Path.cwd() / f"inspeccion_{Path(args.archivo).stem}"
    comando = "python -m impactcal.inspeccion " + shlex.join(
        argv if argv is not None else sys.argv[1:]
    )
    tabla = inspect_dataset(
        df,
        out,
        time_col=args.tiempo,
        group_cols=tuple(args.grupo),
        ratios=tuple(tuple(r) for r in args.razon),
        threshold=args.umbral,
        source=Path(args.archivo).name,
        profile=args.perfil,
        command=comando,
    )
    print(f"{len(tabla)} hallazgos → {out / 'hallazgos.csv'}")
    if not tabla.empty:
        print(tabla.head(10).to_string(index=False, max_colwidth=40))
    print(f"Resumen: {out / 'resumen.md'}")


if __name__ == "__main__":
    main()
