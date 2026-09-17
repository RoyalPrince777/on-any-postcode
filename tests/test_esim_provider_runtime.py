import pytest

from mission_control import esim_provider_runtime, esim_provisioning


class Provider:
    name = "carrier-adapter"

    def provision(self, *, request_id: str, subject_id: str) -> dict:
        return {"provider_profile_id": "profile-1", "active": True}

    def suspend(self, *, provider_profile_id: str) -> dict:
        return {"suspended": True}

    def resume(self, *, provider_profile_id: str) -> dict:
        return {"active": True}

    def revoke(self, *, provider_profile_id: str) -> dict:
        return {"revoked": True}


def teardown_function():
    esim_provisioning.CORE.provider = None


def test_provider_attach_requires_founder_identity():
    with pytest.raises(PermissionError, match="founder_approval_required"):
        esim_provider_runtime.attach_provider(Provider(), founder_identity="")


def test_provider_attachment_is_explicit_and_redacted():
    state = esim_provider_runtime.attach_provider(
        Provider(), founder_identity="founder"
    )

    assert state["configured"] is True
    assert state["provider"] == "carrier-adapter"
    assert state["human_authority_final"] is True
    assert state["credentials_exposed"] is False
    assert esim_provisioning.CORE.provider is not None

    detached = esim_provider_runtime.detach_provider(founder_identity="founder")
    assert detached["configured"] is False
    assert esim_provisioning.CORE.provider is None
