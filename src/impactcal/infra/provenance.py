"""Raw-artifact provenance (`_procedencia.json`, CAL-GEN-03) — the HAZ-arm
convention carried over verbatim: every raw file gets URL/dataset, sha256,
bytes, date; plus version/DOI/request where applicable. Idempotent pipelines
verify against it and skip intact files.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path, chunk: int = 2**20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while blk := f.read(chunk):
            h.update(blk)
    return h.hexdigest()


def write_provenance(artifact: Path, source: str, **extra: Any) -> Path:
    """Write `<artifact>._procedencia.json` next to the artifact."""
    record = {
        "archivo": artifact.name,
        "fuente": source,
        "sha256": _sha256(artifact),
        "bytes": artifact.stat().st_size,
        "fecha_descarga": dt.datetime.now(dt.timezone.utc).isoformat(),
        **extra,
    }
    path = artifact.with_name(artifact.name + "._procedencia.json")
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def verify_provenance(artifact: Path) -> bool:
    """True iff the artifact exists and matches its recorded sha256."""
    prov = artifact.with_name(artifact.name + "._procedencia.json")
    if not (artifact.exists() and prov.exists()):
        return False
    record = json.loads(prov.read_text(encoding="utf-8"))
    return record.get("sha256") == _sha256(artifact)
