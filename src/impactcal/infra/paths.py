"""Central path resolution (CAL-GEN-06): no CWD-relative paths anywhere.

The repo root is auto-detected (presence of pyproject.toml); bulk data may live
outside the repo — set `data_root` in configs/calibracion.yaml or the
IMPACTCAL_DATA_ROOT environment variable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _find_repo_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__)).resolve()
    for parent in [p, *p.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Repo root not found (no pyproject.toml upwards).")


@dataclass(frozen=True)
class ProjectPaths:
    root: Path = field(default_factory=_find_repo_root)

    @property
    def data(self) -> Path:
        env = os.environ.get("IMPACTCAL_DATA_ROOT")
        return Path(env).expanduser() if env else self.root / "data"

    @property
    def configs(self) -> Path:
        return self.root / "configs"

    @property
    def results(self) -> Path:
        return self.root / "results"

    @property
    def manifests(self) -> Path:
        return self.results / "manifests"

    def hazard(self, name: str) -> Path:
        """data/<hazard>/{crudos,consolidados} convention (DC-CONV-1)."""
        return self.data / name
