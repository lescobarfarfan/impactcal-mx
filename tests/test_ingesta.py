"""Unit + end-to-end tests for frozen-input ingestion (CAL-GEN-02/12)."""

import pytest

from impactcal.infra.freeze import freeze_copy
from impactcal.infra.provenance import verify_provenance
from impactcal.target.cenapred import CONSOLIDADOS, ingest_cenapred, verify_cenapred


def test_freeze_copy_roundtrip(tmp_path):
    src = tmp_path / "origen" / "dato.csv"
    src.parent.mkdir()
    src.write_text("a,b\n1,2\n")
    dest_dir = tmp_path / "data" / "fuente"

    dest = freeze_copy(src, dest_dir, source="unit-test")
    assert dest.read_text() == "a,b\n1,2\n"
    assert verify_provenance(dest)

    # Idempotent: intact destination is not rewritten.
    antes = dest.stat().st_mtime_ns
    assert freeze_copy(src, dest_dir, source="unit-test") == dest
    assert dest.stat().st_mtime_ns == antes

    # Corrupted destination is restored on the next pass.
    dest.write_text("corrupto")
    freeze_copy(src, dest_dir, source="unit-test")
    assert dest.read_text() == "a,b\n1,2\n" and verify_provenance(dest)


def test_freeze_copy_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        freeze_copy(tmp_path / "no_existe.csv", tmp_path / "data", source="unit-test")


def test_ingest_cenapred_end_to_end(tmp_path):
    source = tmp_path / "climateCCR"
    source.mkdir()
    for nombre in CONSOLIDADOS:
        (source / nombre).write_text(f"columna\n{nombre}\n")
    dest = tmp_path / "data" / "cenapred" / "consolidados"

    frozen = ingest_cenapred(source, dest)
    assert [p.name for p in frozen] == list(CONSOLIDADOS)
    assert all(verify_cenapred(dest).values())

    (dest / CONSOLIDADOS[0]).write_text("alterado\n")
    assert not verify_cenapred(dest)[CONSOLIDADOS[0]]
