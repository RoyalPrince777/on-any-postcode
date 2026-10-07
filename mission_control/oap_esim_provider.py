"""OAP-owned adapter between the eSIM lifecycle and SM-DP+ boundary.

The adapter deliberately exposes the legacy EsimProvider contract while keeping
profile preparation first-party. Production suspension/resume/revocation remain
fail-closed until the secure backend implements matching lifecycle controls.
"""
from __future__ import annotations

from .oap_smdp import OapSmdpDevelopmentBoundary


class OapFirstPartyEsimProvider:
    name = "oap-first-party-smdp"

    def __init__(self, smdp: OapSmdpDevelopmentBoundary) -> None:
        self.smdp = smdp

    def provision(self, *, request_id: str, subject_id: str) -> dict:
        result = self.smdp.prepare(profile_ref=request_id, subject_id=subject_id)
        profile_ref = str(result.get("profile_ref") or "").strip()
        attestation = str(result.get("backend_attestation") or "").strip()
        if result.get("state") != "profile_created" or not profile_ref or not attestation:
            raise RuntimeError("first_party_profile_creation_not_confirmed")
        # Existing lifecycle field name is retained for schema compatibility.
        # The value is an OAP-owned opaque profile reference, never secret material.
        return {"provider_profile_id": profile_ref}

    def suspend(self, *, provider_profile_id: str) -> dict:
        raise RuntimeError("first_party_profile_suspend_not_implemented")

    def resume(self, *, provider_profile_id: str) -> dict:
        raise RuntimeError("first_party_profile_resume_not_implemented")

    def revoke(self, *, provider_profile_id: str) -> dict:
        raise RuntimeError("first_party_profile_revoke_not_implemented")
