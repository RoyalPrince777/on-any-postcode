from mission_control.esim_provisioning import EsimProvisioningCore
from mission_control.oap_esim_provider import OapFirstPartyEsimProvider
from mission_control.oap_smdp import OapSmdpDevelopmentBoundary


class SafeBackend:
    def prepare_profile(self, *, profile_ref: str, subject_id: str) -> dict:
        return {
            "profile_prepared": True,
            "backend_attestation": "opaque-attestation",
        }


def test_first_party_smdp_drives_existing_lifecycle_to_available_only():
    provider = OapFirstPartyEsimProvider(OapSmdpDevelopmentBoundary(SafeBackend()))
    core = EsimProvisioningCore(provider=provider)
    requested = core.request(subject_id="founder", purpose="for-me-first")
    approved = core.approve(requested["request_id"], founder_identity="founder")
    assert approved["state"] == "approved"

    available = core.provision(requested["request_id"])
    assert available["state"] == "available"
    assert available["provider_name"] == "oap-first-party-smdp"
    assert available["provider_profile_id"] == requested["request_id"]
    assert available["state"] != "active"


def test_first_party_provider_lifecycle_controls_fail_closed_until_built():
    provider = OapFirstPartyEsimProvider(OapSmdpDevelopmentBoundary(SafeBackend()))
    for operation in (provider.suspend, provider.resume, provider.revoke):
        try:
            operation(provider_profile_id="OAP-ESIM-000001")
        except RuntimeError as exc:
            assert "not_implemented" in str(exc)
        else:
            raise AssertionError("unimplemented secure lifecycle operation must fail closed")
