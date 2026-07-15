"""Unit tests for the frozen TC hazard generation (CAL-WIND-03) — no CLIMADA needed."""

import pandas as pd
import pytest

from impactcal.hazard.tc import ensure_ibtracs_cache, select_storms
from impactcal.infra.provenance import write_provenance


def _frozen_nc(tmp_path, contenido=b"congelado"):
    frozen = tmp_path / "crudos" / "IBTrACS.ALL.v04r01.nc"
    frozen.parent.mkdir()
    frozen.write_bytes(contenido)
    write_provenance(frozen, source="test")
    return frozen


def test_ensure_ibtracs_cache_restores_divergent_cache(tmp_path):
    frozen = _frozen_nc(tmp_path)
    cache = tmp_path / "cache" / "IBTrACS.ALL.v04r01.nc"
    cache.parent.mkdir()
    cache.write_bytes(b"divergente")

    sha = ensure_ibtracs_cache(frozen, cache)

    assert cache.read_bytes() == b"congelado"
    assert len(sha) == 64


def test_ensure_ibtracs_cache_creates_missing_cache(tmp_path):
    frozen = _frozen_nc(tmp_path)
    cache = tmp_path / "cache" / "IBTrACS.ALL.v04r01.nc"

    ensure_ibtracs_cache(frozen, cache)

    assert cache.read_bytes() == b"congelado"


def test_ensure_ibtracs_cache_rejects_corrupt_frozen(tmp_path):
    frozen = _frozen_nc(tmp_path)
    frozen.write_bytes(b"alterado tras congelar")

    with pytest.raises(RuntimeError, match="congelada"):
        ensure_ibtracs_cache(frozen, tmp_path / "cache.nc")


def test_select_storms_filters_bbox_and_season():
    index = pd.DataFrame(
        {
            "sid": ["a", "b", "c"],
            "season": [2005, 2005, 2025],
            "toca_mexico": [True, False, True],  # b lejos de México; c temporada incompleta
        }
    )
    assert select_storms(index, temporada_max=2024) == ["a"]
