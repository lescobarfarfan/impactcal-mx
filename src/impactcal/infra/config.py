"""YAML configuration loading (CAL-GEN-06): parameters over hard-coding.

All parameters live in `configs/calibracion.yaml`; every pipeline resolves its
config through here so the run manifest can record it verbatim.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from impactcal.infra.paths import ProjectPaths


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load the calibration config (default: `configs/calibracion.yaml`)."""
    p = path or ProjectPaths().configs / "calibracion.yaml"
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
