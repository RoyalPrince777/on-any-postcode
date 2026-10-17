"""OAP Music metadata batch admission and no-write guarantee."""
import pytest

from mission_control.music_import_plan import (
    MAX_IMPORT_BATCH_RECORDS,
    plan_catalogue_batch,
)


def test_unconfigured_storage_blocks_batch(monkeypatch):
    monkeypatch.delenv("OAP_DATA_STORAGE_ROOT", raising=False)
    result = plan_catalogue_batch(record_count=100)
    assert result["planned_bytes"] == 307200
    assert result["write_authorized"] is False
    assert result["storage_preflight"]["reason"] == "capacity_unverified"


def test_batch_limit():
    with pytest.raises(ValueError):
        plan_catalogue_batch(record_count=MAX_IMPORT_BATCH_RECORDS + 1)


def test_negative_and_boolean_counts_rejected():
    for count in (-1, True):
        with pytest.raises(TypeError if isinstance(count, bool) else ValueError):
            plan_catalogue_batch(record_count=count)
