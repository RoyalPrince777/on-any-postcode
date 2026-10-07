"""First-party OAP SM-DP+ development boundary.

This is deliberately a control-plane contract, not a production GSMA SM-DP+
implementation. It stores only non-secret profile metadata and fails closed unless
an injected secure backend performs the cryptographic/profile operation.
"""
from __future__ import annotations

import dataclasses
import typing


class SecureProfileBackend(typing.Protocol):
    """Isolated backend contract. Secret key material must not cross this boundary."""

    def prepare_profile(self, *, profile_ref: str, subject_id: str) -> dict: ...


@dataclasses.dataclass(frozen=True)
class ProfileMetadata:
    profile_ref: str
    subject_id: str
    state: str
    backend_attestation: str


class OapSmdpDevelopmentBoundary:
    """Non-secret orchestration boundary for first-party profile preparation."""

    def __init__(self, backend: SecureProfileBackend | None = None) -> None:
        self.backend = backend

    def prepare(self, *, profile_ref: str, subject_id: str) -> dict:
        profile_ref = str(profile_ref or "").strip()
        subject_id = str(subject_id or "").strip()
        if not profile_ref:
            raise ValueError("profile_ref_required")
        if not subject_id:
            raise ValueError("subject_id_required")
        if self.backend is None:
            raise RuntimeError("secure_profile_backend_not_configured")

        result = self.backend.prepare_profile(
            profile_ref=profile_ref,
            subject_id=subject_id,
        )
        attestation = str(result.get("backend_attestation") or "").strip()
        if result.get("profile_prepared") is not True or not attestation:
            raise RuntimeError("profile_preparation_not_confirmed")

        # Never accept profile/authentication/key material back into the control plane.
        forbidden = {
            "ki", "opc", "op", "k", "private_key", "profile_secret",
            "authentication_key", "secret", "activation_code",
        }
        if forbidden.intersection(str(key).lower() for key in result):
            raise RuntimeError("secret_material_crossed_boundary")

        return dataclasses.asdict(
            ProfileMetadata(
                profile_ref=profile_ref,
                subject_id=subject_id,
                state="profile_created",
                backend_attestation=attestation,
            )
        )


BOUNDARY = OapSmdpDevelopmentBoundary()
