"""Focused fail-closed contract checks for the OAP Music company registry."""
import pytest

from mission_control import music_company_rights_registry as registry
from mission_control import music_civilization_migration


def test_registry_migration_is_governed_not_request_time():
    assert music_civilization_migration._MIGRATIONS[-1][0] == registry.MIGRATION_VERSION
    assert registry.MIGRATION_VERSION == "0015_music_company_rights_registry"
    ddl = "\n".join(registry.SCHEMA_STATEMENTS)
    assert "owner_identity_id UUID NOT NULL" in ddl
    assert "UNIQUE(owner_identity_id,kind,reference)" in ddl
    assert "reviewer_identity_id IS NOT NULL" in ddl
    assert "evidence_sha256 IS NOT NULL" in ddl


def test_registry_rejects_invalid_kind_and_evidence():
    with pytest.raises(ValueError, match="invalid_registry_kind"):
        registry.validate_record(kind="fake_membership", reference="x", display_name="x")
    with pytest.raises(ValueError, match="invalid_evidence_sha256"):
        registry.validate_record(kind="company", reference="14753133",
                                 display_name="ON ANY POSTCODE LTD",
                                 evidence_sha256="invalid", evidence_reference="document")


def test_registry_never_infers_company_or_music_authority():
    item = registry.validate_record(kind="company", reference="14753133",
                                    display_name="ON ANY POSTCODE LTD")
    assert item[3:] == (None, None)
    with pytest.raises(PermissionError, match="review_authority_not_wired"):
        registry.MusicCompanyRightsRegistry().review(
            owner_identity_id="00000000-0000-0000-0000-000000000001",
            registry_id="00000000-0000-0000-0000-000000000002",
            reviewer_identity_id="00000000-0000-0000-0000-000000000003",
            decision="VERIFIED",
        )
