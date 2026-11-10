from mission_control.oap_smdp import OapSmdpDevelopmentBoundary


class SafeBackend:
    def prepare_profile(self, *, profile_ref: str, subject_id: str) -> dict:
        return {"profile_prepared": True, "backend_attestation": "dev-attestation-1"}


class LeakyBackend:
    def prepare_profile(self, *, profile_ref: str, subject_id: str) -> dict:
        return {
            "profile_prepared": True,
            "backend_attestation": "bad",
            "ki": "must-never-enter-control-plane",
        }


def test_smdp_boundary_fails_closed_without_secure_backend():
    boundary = OapSmdpDevelopmentBoundary()
    try:
        boundary.prepare(profile_ref="OAP-ESIM-000001", subject_id="founder")
    except RuntimeError as exc:
        assert str(exc) == "secure_profile_backend_not_configured"
    else:
        raise AssertionError("SM-DP+ boundary must fail closed")


def test_smdp_boundary_returns_only_non_secret_metadata():
    boundary = OapSmdpDevelopmentBoundary(SafeBackend())
    result = boundary.prepare(profile_ref="OAP-ESIM-000001", subject_id="founder")
    assert result == {
        "profile_ref": "OAP-ESIM-000001",
        "subject_id": "founder",
        "state": "profile_created",
        "backend_attestation": "dev-attestation-1",
    }


def test_smdp_boundary_rejects_secret_material():
    boundary = OapSmdpDevelopmentBoundary(LeakyBackend())
    try:
        boundary.prepare(profile_ref="OAP-ESIM-000001", subject_id="founder")
    except RuntimeError as exc:
        assert str(exc) == "secret_material_crossed_boundary"
    else:
        raise AssertionError("secret material must never cross into the control plane")
