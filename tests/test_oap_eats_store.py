"""Schema authority checks; pricing/idempotency use real PostgreSQL proofs."""
import pytest

from mission_control import oap_eats_store


def test_eats_schema_requires_explicit_human_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval"):
        oap_eats_store.init_schema()


def test_eats_schema_dry_run_is_not_green():
    status = oap_eats_store.init_schema(assume_yes=True, dry_run=True)
    assert status["schema_ready"] is False
    assert status["human_authority_final"] is True
    assert status["integrity_migration"] == oap_eats_store.INTEGRITY_MIGRATION_VERSION
