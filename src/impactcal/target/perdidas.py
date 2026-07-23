"""Ruta B loss table: CENAPRED total losses per year-state-family (DC-CAL-TARGET-2).

Reduces the frozen CENAPRED panel (`impacto_estado_anio_peril.csv`) to the
calibration target of ruta B: for every (año, estado) inside the panel window
(`periodo.anio_inicial`-`periodo.anio_final`), the total observed loss of the
perils in scope, split by `familia_peril`:

- `ciclonica` — `Ciclón tropical` + `Marejada` (CAL-SCOPE-02 wind/surge side)
- `fluvial`   — `Daños por lluvia` + `Inundación`

`familia_peril` is what CENAPRED *reports*; the attribution rule of
CAL-XWALK-02 (rain-cone events count as cyclone-related) travels separately in
`familia_xwalk`/`flag_revision`, taken from the crosswalk, so the inclusion
mask of `DC-CAL-TARGET-4` can be built without re-deriving anything.

Amounts stay in **current MXN** (DC-CONV-4); the INPC deflation of
CAL-TARGET-03 is a downstream step and adds the `monto_total_mxn_{base}`
column once the index is frozen.

CLI::

    python -m impactcal.target.perdidas [--config RUTA]
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import pandas as pd

from impactcal.infra.config import load_config
from impactcal.infra.manifest import RunManifest
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance
from impactcal.target.crosswalk import ENTIDAD_A_CVE

FAMILIA_POR_PERIL = {
    "Ciclón tropical": "ciclonica",
    "Marejada": "ciclonica",
    "Daños por lluvia": "fluvial",
    "Inundación": "fluvial",
}

MDP_A_MXN = 1e6


def fuente_publicacion(anio: int) -> str:
    """Which CENAPRED publication a year's figures come from (CAL-TARGET-06)."""
    if anio <= 2015:
        return "base_abierta_2000_2015"
    if anio <= 2023:
        return f"extenso_{anio}"
    return f"resumen_{anio}"


def build_perdidas(panel: pd.DataFrame, xwalk: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Aggregate the CENAPRED panel into the ruta B target table."""
    anio_ini = int(config["periodo"]["anio_inicial"])
    anio_fin = config["periodo"].get("anio_final")

    df = panel[panel["peril_canonico"].isin(FAMILIA_POR_PERIL)].copy()
    df["anio"] = df["anio"].astype(int)
    df = df[df["anio"] >= anio_ini]
    if anio_fin:
        df = df[df["anio"] <= int(anio_fin)]

    faltantes = sorted(set(df["entidad"]) - set(ENTIDAD_A_CVE))
    if faltantes:
        raise ValueError(f"entidades sin clave INEGI (DC-CONV-5): {faltantes}")
    df["cve_ent"] = df["entidad"].map(ENTIDAD_A_CVE)
    df["familia_peril"] = df["peril_canonico"].map(FAMILIA_POR_PERIL)

    out = (
        df.groupby(["anio", "cve_ent", "familia_peril"], as_index=False)
        .agg(
            monto_total_mxn_corr=("danio_mdp", lambda s: s.sum() * MDP_A_MXN),
            n_eventos=("n_eventos", "sum"),
            defunciones=("defunciones", "sum"),
        )
        .sort_values(["anio", "cve_ent", "familia_peril"])
    )
    out["fuente_publicacion"] = out["anio"].map(fuente_publicacion)

    cols = ["anio", "cve_ent", "familia_asignada", "flag_revision", "version_crosswalk"]
    out = out.merge(
        xwalk[cols].rename(columns={"familia_asignada": "familia_xwalk"}),
        on=["anio", "cve_ent"],
        how="left",
    )
    return out.reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()
    panel_csv = paths.data / "cenapred" / "consolidados" / "impacto_estado_anio_peril.csv"
    xwalk_csv = paths.data / "crosswalk" / "crosswalk_anio_estado_tormentas.csv"
    for insumo in (panel_csv, xwalk_csv):
        if not verify_provenance(insumo):
            raise RuntimeError(f"insumo corrupto o sin procedencia (CAL-GEN-12): {insumo}")

    panel = pd.read_csv(panel_csv)
    xwalk = pd.read_csv(xwalk_csv, dtype={"cve_ent": str})
    out = build_perdidas(panel, xwalk, config)

    out_dir = paths.data / "target"
    out_dir.mkdir(parents=True, exist_ok=True)
    salida = out_dir / "perdidas_totales_anual.csv"
    out.to_csv(salida, index=False)

    write_provenance(
        salida,
        source="impactcal.target.perdidas (determinista, DC-CAL-TARGET-2)",
        insumos={p.name: _sha256(p) for p in (panel_csv, xwalk_csv)},
        cobertura_anios=f"{out['anio'].min()}-{out['anio'].max()}",
        unidad="MXN corrientes (sin deflactar; INPC pendiente, CAL-TARGET-03)",
        familias=sorted(out["familia_peril"].unique()),
    )

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RunManifest(
        run_id=f"perdidas_rutaB_{ts}",
        seed=int(config["semilla_base"]),
        config=config,
        notes="Tabla objetivo ruta B: determinista (sin RNG); semilla por CAL-GEN-05.",
    ).write(paths.manifests, paths.root)

    print(f"perdidas ruta B: {salida}")
    print(f"  filas: {len(out)} | años: {out['anio'].min()}-{out['anio'].max()}")
    print(f"  estados: {out['cve_ent'].nunique()}")
    for fam, g in out.groupby("familia_peril"):
        miles_mm = g["monto_total_mxn_corr"].sum() / 1e9
        print(f"  {fam}: {len(g)} filas, {miles_mm:,.1f} mil millones MXN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
