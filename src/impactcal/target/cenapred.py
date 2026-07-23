"""CENAPRED total-loss ingestion (ruta B target; upstream of DC-CAL-TARGET-2).

Freezes the consolidated outputs of the climateCCR CENAPRED pipeline into
`data/cenapred/consolidados/` with per-file provenance (CAL-GEN-02/12):

- `impacto_estado_anio_peril.csv`   — panel (entidad, año, peril canónico), ESTRUCTURA A
- `eventos_cenapred_climada.csv`    — event-level table, ESTRUCTURA B
- `impacto_multiestado.csv`         — multi-state events excluded from A (never split)
- `catalogo_fenomenos_climaticos.csv` — (evento climático × estado) occurrence catalog

The raw files (open CSV 2000-2015, EXTENSO/RESUMEN PDFs) and the scraper stay
in the climateCCR repo; each sidecar records the absolute origin path.
Machine-readable coverage: **2000-2024** — the open CSV 2000-2015 plus the
structured captures of the extenso reports 2016-2023 and the resumen ejecutivo
2024 (`data/cenapred/pdfs_procesados_2016-2024/`, CAL-TARGET-06). 2024 carries
only resumen-level detail (5 estados en alcance) and is excluded from the
calibration panel via `periodo.anio_final` — see `DC-CAL-TARGET-2`.

CLI (Spanish flags verbatim, CAL-GEN-08)::

    python -m impactcal.target.cenapred [--modo ingerir|verificar] [--forzar] [--config RUTA]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from impactcal.infra.config import load_config
from impactcal.infra.freeze import freeze_copy
from impactcal.infra.paths import ProjectPaths
from impactcal.infra.provenance import verify_provenance

CONSOLIDADOS = (
    "impacto_estado_anio_peril.csv",
    "eventos_cenapred_climada.csv",
    "impacto_multiestado.csv",
    "catalogo_fenomenos_climaticos.csv",
)

_FUENTE = "CENAPRED — Impacto socioeconómico de desastres (consolidados del pipeline climateCCR)"


def ingest_cenapred(source_dir: Path, dest_dir: Path, *, force: bool = False) -> list[Path]:
    """Freeze the four CENAPRED consolidados into `dest_dir` with provenance."""
    return [
        freeze_copy(
            source_dir / nombre,
            dest_dir,
            source=_FUENTE,
            force=force,
            cobertura_anios="2000-2024",
            nota=(
                "Extensos 2016-2023 + resumen 2024 capturados (CAL-TARGET-06); "
                "2024 preliminar, fuera del panel de calibración."
            ),
        )
        for nombre in CONSOLIDADOS
    ]


def verify_cenapred(dest_dir: Path) -> dict[str, bool]:
    """Checksum verification of the frozen consolidados (no copying)."""
    return {nombre: verify_provenance(dest_dir / nombre) for nombre in CONSOLIDADOS}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--modo", choices=["ingerir", "verificar"], default="ingerir")
    parser.add_argument("--forzar", action="store_true", help="re-copia aunque verifique")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = ProjectPaths()
    source_dir = Path(config["fuentes_externas"]["cenapred_consolidados"]).expanduser()
    dest_dir = paths.data / "cenapred" / "consolidados"

    if args.modo == "verificar":
        estado = verify_cenapred(dest_dir)
        for nombre, ok in estado.items():
            print(f"{'OK ' if ok else 'FALLA'} {nombre}")
        return 0 if all(estado.values()) else 1

    frozen = ingest_cenapred(source_dir, dest_dir, force=args.forzar)
    for p in frozen:
        print(f"congelado: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
