"""Unit tests for the timestep-convergence metrics (OQ-CAL-01) — no CLIMADA needed."""

import numpy as np

from impactcal.hazard.timestep_test import swath_metrics


def test_swath_metrics_identical():
    v = np.array([0.0, 10.0, 30.0, 50.0])
    m = swath_metrics(v, v, v_thresh=25.7)
    assert m["rmse_ms"] == 0.0 and m["bias_ms"] == 0.0 and m["max_abs_ms"] == 0.0
    assert m["celdas_thresh_ref"] == m["celdas_thresh_alt"] == 2


def test_swath_metrics_known_difference():
    ref = np.array([0.0, 20.0, 30.0])
    alt = np.array([0.0, 26.0, 24.0])  # +6 y -6 en las dos celdas tocadas
    m = swath_metrics(ref, alt, v_thresh=25.7)
    assert np.isclose(m["rmse_ms"], 6.0)
    assert np.isclose(m["bias_ms"], 0.0)
    assert np.isclose(m["max_abs_ms"], 6.0)
    assert m["max_int_ref_ms"] == 30.0 and m["max_int_alt_ms"] == 26.0
    # el swath alterno pierde la celda dañina (30→24) pero gana otra (20→26)
    assert m["celdas_thresh_ref"] == 1 and m["celdas_thresh_alt"] == 1


def test_swath_metrics_empty():
    z = np.zeros(4)
    m = swath_metrics(z, z, v_thresh=25.7)
    assert m["rmse_ms"] == 0.0 and m["celdas_thresh_ref"] == 0
