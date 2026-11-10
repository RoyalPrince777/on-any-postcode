"""OAP-owned adapter between governed eSIM lifecycle and SM-DP+."""
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
        return {"provider_profile_id": profile_ref}

    def suspend(self, *, provider_profile_id: str) -> dict:
        result = self.smdp.suspend(profile_ref=provider_profile_id)
        return {"suspended": result.get("suspended") is True}

    def resume(self, *, provider_profile_id: str) -> dict:
        result = self.smdp.resume(profile_ref=provider_profile_id)
        # Legacy lifecycle expects this key. It confirms profile resume only;
        # EsimProvisioningCore still moves merely to AVAILABLE and requires
        # independent network evidence before ACTIVE.
        return {"active": result.get("resumed") is True}

    def revoke(self, *, provider_profile_id: str) -> dict:
        result = self.smdp.revoke(profile_ref=provider_profile_id)
        return {"revoked": result.get("revoked") is True}
