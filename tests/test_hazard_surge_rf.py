"""Unit tests for the frozen surge/RF hazard generation — no CLIMADA needed."""

import numpy as np
import pytest
from scipy import sparse

from impactcal.hazard.rf import isimip_pair, sanitize_nan, select_years
from impactcal.hazard.surge import load_frozen
from impactcal.infra.provenance import write_provenance


def _touch_isimip(tmp_path, variable, proteccion, n=1):
    for i in range(n):
        (
            tmp_path / f"cama-flood_matsiro_gswp3_x{i}_{variable}_{proteccion}_150arcsec.nc4"
        ).write_bytes(b"nc")


def test_isimip_pair_selects_one_pair_per_protection(tmp_path):
    for variable in ("flddph", "fldfrc"):
        for prot in ("none", "flopros"):
            _touch_isimip(tmp_path, variable, prot)

    dph, frc = isimip_pair(tmp_path, "none")
    assert "_flddph_none_" in dph.name and "_fldfrc_none_" in frc.name


def test_isimip_pair_rejects_missing_or_ambiguous(tmp_path):
    with pytest.raises(RuntimeError, match="flddph/none"):
        isimip_pair(tmp_path, "none")
    _touch_isimip(tmp_path, "flddph", "none", n=2)
    with pytest.raises(RuntimeError, match="hay 2"):
        isimip_pair(tmp_path, "none")


def test_select_years_cuts_at_panel_start():
    assert select_years([1971, 1999, 2000, 2010], anio_inicial=2000) == [2000, 2010]
    with pytest.raises(RuntimeError, match="no cubre"):
        select_years([1971, 1999], anio_inicial=2000)


class _HazStub:
    def __init__(self):
        self.intensity = sparse.csr_matrix(np.array([[np.nan, 1.5], [0.0, np.nan]]))
        self.fraction = sparse.csr_matrix(np.array([[np.nan, 0.5], [0.0, 0.0]]))


def test_sanitize_nan_zeroes_and_counts():
    haz = _HazStub()
    assert sanitize_nan(haz) == 2  # dos celdas nan en intensity, una en fraction
    assert not np.isnan(haz.intensity.data).any() and not np.isnan(haz.fraction.data).any()
    assert haz.intensity[0, 1] == 1.5 and haz.fraction[0, 1] == 0.5


def test_load_frozen_rejects_unverified_input(tmp_path):
    artefacto = tmp_path / "haz_tc.h5"
    artefacto.write_bytes(b"h5")
    with pytest.raises(RuntimeError, match="congelado"):
        load_frozen(artefacto, "Hazard viento congelado")  # sin procedencia

    write_provenance(artefacto, source="test")
    assert load_frozen(artefacto, "Hazard viento congelado") == artefacto
