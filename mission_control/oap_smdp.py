"""First-party OAP SM-DP+ development boundary.

Control-plane contract only. Secret profile/authentication material stays behind the
injected secure backend; this module accepts only opaque attestations.
"""
from __future__ import annotations

import dataclasses
import typing


class SecureProfileBackend(typing.Protocol):
    def prepare_profile(self, *, profile_ref: str, subject_id: str) -> dict: ...
    def suspend_profile(self, *, profile_ref: str) -> dict: ...
    def resume_profile(self, *, profile_ref: str) -> dict: ...
    def revoke_profile(self, *, profile_ref: str) -> dict: ...


@dataclasses.dataclass(frozen=True)
class ProfileMetadata:
    profile_ref: str
    subject_id: str
    state: str
    backend_attestation: str


class OapSmdpDevelopmentBoundary:
    def __init__(self, backend: SecureProfileBackend | None = None) -> None:
        self.backend = backend

    @staticmethod
    def _validate_result(result: dict, *, confirmation: str) -> str:
        forbidden = {
            "ki", "opc", "op", "k", "private_key", "profile_secret",
            "authentication_key", "secret", "activation_code",
        }
        if forbidden.intersection(str(key).lower() for key in result):
            raise RuntimeError("secret_material_crossed_boundary")
        attestation = str(result.get("backend_attestation") or "").strip()
        if result.get(confirmation) is not True or not attestation:
            raise RuntimeError(f"{confirmation}_not_confirmed")
        return attestation

    def _require_backend(self) -> SecureProfileBackend:
        if self.backend is None:
            raise RuntimeError("secure_profile_backend_not_configured")
        return self.backend

    def prepare(self, *, profile_ref: str, subject_id: str) -> dict:
        profile_ref = str(profile_ref or "").strip()
        subject_id = str(subject_id or "").strip()
        if not profile_ref:
            raise ValueError("profile_ref_required")
        if not subject_id:
            raise ValueError("subject_id_required")
        result = self._require_backend().prepare_profile(
            profile_ref=profile_ref, subject_id=subject_id
        )
        attestation = self._validate_result(result, confirmation="profile_prepared")
        return dataclasses.asdict(ProfileMetadata(
            profile_ref=profile_ref,
            subject_id=subject_id,
            state="profile_created",
            backend_attestation=attestation,
        ))

    def suspend(self, *, profile_ref: str) -> dict:
        result = self._require_backend().suspend_profile(profile_ref=profile_ref)
        return {"suspended": True, "backend_attestation": self._validate_result(
            result, confirmation="profile_suspended"
        )}

    def resume(self, *, profile_ref: str) -> dict:
        result = self._require_backend().resume_profile(profile_ref=profile_ref)
        return {"resumed": True, "backend_attestation": self._validate_result(
            result, confirmation="profile_resumed"
        )}

    def revoke(self, *, profile_ref: str) -> dict:
        result = self._require_backend().revoke_profile(profile_ref=profile_ref)
        return {"revoked": True, "backend_attestation": self._validate_result(
            result, confirmation="profile_revoked"
        )}


BOUNDARY = OapSmdpDevelopmentBoundary()
