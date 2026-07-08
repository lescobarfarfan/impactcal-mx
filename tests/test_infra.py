"""Unit tests for the reproducibility layer (CAL-GEN-04/05/06)."""

import json

import numpy as np
import pytest

from impactcal.infra import ProjectPaths, RunManifest, set_seed, get_rng
from impactcal.infra.provenance import verify_provenance, write_provenance


def test_seed_required():
    import impactcal.infra.seeds as s

    s._GLOBAL_SEED = None
    with pytest.raises(RuntimeError):
        get_rng()


def test_streams_reproducible_and_independent():
    set_seed(123)
    a1 = get_rng("viento").standard_normal(5)
    b1 = get_rng("marejada").standard_normal(5)
    set_seed(123)
    a2 = get_rng("viento").standard_normal(5)
    b2 = get_rng("marejada").standard_normal(5)
    np.testing.assert_array_equal(a1, a2)
    np.testing.assert_array_equal(b1, b2)
    assert not np.allclose(a1, b1)


def test_manifest_roundtrip(tmp_path):
    m = RunManifest(run_id="test_run", seed=7, config={"a": 1})
    p = m.write(tmp_path, repo_root=ProjectPaths().root)
    payload = json.loads(p.read_text())
    assert payload["seed"] == 7 and payload["config"] == {"a": 1}
    assert "numpy" in payload["package_versions"]


def test_provenance_roundtrip(tmp_path):
    f = tmp_path / "dato.csv"
    f.write_text("a,b\n1,2\n")
    write_provenance(f, source="unit-test")
    assert verify_provenance(f)
    f.write_text("a,b\n1,3\n")
    assert not verify_provenance(f)
