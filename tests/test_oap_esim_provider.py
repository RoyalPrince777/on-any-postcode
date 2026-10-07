from mission_control.esim_provisioning import EsimProvisioningCore
from mission_control.oap_esim_provider import OapFirstPartyEsimProvider
from mission_control.oap_smdp import OapSmdpDevelopmentBoundary


class SafeBackend:
    def prepare_profile(self, *, profile_ref: str, subject_id: str) -> dict:
        return {"profile_prepared": True, "backend_attestation": "prepared"}
    def suspend_profile(self, *, profile_ref: str) -> dict:
        return {"profile_suspended": True, "backend_attestation": "suspended"}
    def resume_profile(self, *, profile_ref: str) -> dict:
        return {"profile_resumed": True, "backend_attestation": "resumed"}
    def revoke_profile(self, *, profile_ref: str) -> dict:
        return {"profile_revoked": True, "backend_attestation": "revoked"}


def _available_core():
    provider = OapFirstPartyEsimProvider(OapSmdpDevelopmentBoundary(SafeBackend()))
    core = EsimProvisioningCore(provider=provider)
    item = core.request(subject_id="founder", purpose="for-me-first")
    core.approve(item["request_id"], founder_identity="founder")
    return core, core.provision(item["request_id"])


def test_first_party_smdp_drives_existing_lifecycle_to_available_only():
    _, available = _available_core()
    assert available["state"] == "available"
    assert available["provider_name"] == "oap-first-party-smdp"
    assert available["provider_profile_id"] == available["request_id"]
    assert available["state"] != "active"


def test_secure_suspend_resume_requires_fresh_network_truth():
    core, available = _available_core()
    active = core.confirm_network_registration(
        available["request_id"], evidence_id="network-proof-1", session_established=True
    )
    assert active["state"] == "active"
    assert core.suspend(active["request_id"])["state"] == "suspended"
    resumed = core.resume(active["request_id"])
    assert resumed["state"] == "available"
    assert resumed["state"] != "active"


def test_secure_revoke_is_terminal():
    core, available = _available_core()
    revoked = core.revoke(available["request_id"])
    assert revoked["state"] == "revoked"
