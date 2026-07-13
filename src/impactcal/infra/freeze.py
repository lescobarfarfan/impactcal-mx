"""Frozen-input ingestion (CAL-GEN-02, CAL-GEN-12).

External artifacts (e.g. the CENAPRED consolidados produced in the climateCCR
repo, IBTrACS raw CSVs) are copied into this repo's `data/<fuente>/` layout,
hashed, and pinned with a per-artifact `_procedencia.json` sidecar recording
the absolute origin path. Idempotent: a destination file that verifies against
its sidecar is skipped unless `force=True`.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from impactcal.infra.provenance import _sha256, verify_provenance, write_provenance


def freeze_copy(
    src: Path, dest_dir: Path, source: str, *, force: bool = False, **extra: Any
) -> Path:
    """Copy `src` into `dest_dir`, verify the copy's sha256, write provenance.

    Returns the destination path. Raises if the source is missing or the copy
    does not hash-match the origin.
    """
    if not src.exists():
        raise FileNotFoundError(f"Insumo externo no encontrado: {src}")
    dest = dest_dir / src.name
    if dest.exists() and not force and verify_provenance(dest):
        return dest
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    sha_origen = _sha256(src)
    if _sha256(dest) != sha_origen:
        raise OSError(f"Copia corrupta (sha256 no coincide con el origen): {dest}")
    write_provenance(dest, source=source, origen=str(src.resolve()), **extra)
    return dest
