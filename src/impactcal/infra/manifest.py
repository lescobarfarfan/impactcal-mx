"""Run manifests (CAL-GEN-05): every stochastic or calibration run writes one.

Captures: resolved config, git commit, seed, package versions, timestamps.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

_PINNED = ("numpy", "pandas", "climada", "climada-petals", "pymc", "arviz", "geopandas", "xarray")


def _git_commit(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True
        )
        return out.stdout.strip() + ("+dirty" if dirty.stdout.strip() else "")
    except Exception:
        return "NO_GIT"


def _versions() -> dict[str, str]:
    vers: dict[str, str] = {}
    for pkg in _PINNED:
        try:
            vers[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            vers[pkg] = "not-installed"
    return vers


@dataclass
class RunManifest:
    run_id: str
    seed: int
    config: dict[str, Any]
    notes: str = ""
    started_at: str = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc).isoformat())

    def write(self, manifests_dir: Path, repo_root: Path) -> Path:
        manifests_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": self.run_id,
            "seed": self.seed,
            "git_commit": _git_commit(repo_root),
            "package_versions": _versions(),
            "config": self.config,
            "notes": self.notes,
            "started_at": self.started_at,
            "written_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        path = manifests_dir / f"{self.run_id}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
