"""First-party OAP Global Affairs evidence and authority control plane.

Reuses the existing owner-scoped Organiser/governance workspace and canonical
audit_events chain. It does not create diplomatic status, immunity, a new
database, or a parallel identity system.

Truth boundaries:
- Organiser = what OAP is doing.
- Registry = what evidence supports.
- Authority Matrix = what an OAP representative may do internally.
- OAP approval never promotes an internal role into government accreditation.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from hashlib import sha256
from typing import Any
from uuid import UUID

from mission_control import workspaces

_LIMIT = 100
_PREFIX = "OAP-GLOBAL-AFFAIRS:"
_RECORD_TYPES = frozenset({"evidence", "authority", "mission", "credential"})
_EVIDENCE_STATES = frozenset({
    "DRAFT", "UNVERIFIED", "UNDER_REVIEW", "VERIFIED", "RECOGNISED",
    "ACCREDITED", "EXPIRED", "REVOKED", "DISPUTED", "BLOCKED",
})
_EVIDENCE_CLASSES = frozenset({"A", "B", "C", "D", "E"})
_DECISIONS = frozenset({"ALLOW", "REVIEW", "BLOCK"})
_EXTERNAL_ONLY_PERMISSIONS = frozenset({
    "claim_diplomatic_status",
    "claim_diplomatic_immunity",
    "act_as_diplomat",
    "issue_diplomatic_credential",
    "operate_embassy_or_consulate",
})


class GlobalAffairsUnavailable(RuntimeError):
    """Raised when Global Affairs history cannot be proven complete."""


def _owner(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_global_affairs_owner_required") from exc


def _record_id(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("canonical_global_affairs_record_id_required") from exc


def _digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    subject_ref: str
    claim_type: str
    claim_text: str
    status: str
    evidence_class: str
    issuer: str = ""
    jurisdiction: str = ""
    evidence_ref: str = ""
    evidence_hash: str = ""
    effective_date: str = ""
    expiry_date: str = ""
    verification_method: str = ""
    externally_recognised: bool = False
    diplomatic_status_claimed: bool = False

    def __post_init__(self) -> None:
        for value, error, limit in (
            (self.subject_ref, "subject_ref_required", 160),
            (self.claim_type, "claim_type_required", 80),
            (self.claim_text, "claim_text_required", 500),
        ):
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(error)
        if self.status not in _EVIDENCE_STATES:
            raise ValueError("invalid_evidence_status")
        if self.evidence_class not in _EVIDENCE_CLASSES:
            raise ValueError("invalid_evidence_class")
        if self.evidence_hash and (
            len(self.evidence_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in self.evidence_hash)
        ):
            raise ValueError("invalid_evidence_hash")
        for raw in (self.effective_date, self.expiry_date):
            if raw:
                try:
                    date.fromisoformat(raw)
                except ValueError as exc:
                    raise ValueError("invalid_evidence_date") from exc
        if self.externally_recognised and self.evidence_class not in {"A", "B", "C"}:
            raise ValueError("recognition_requires_stronger_evidence")
        if self.status == "RECOGNISED" and not self.externally_recognised:
            raise ValueError("recognised_status_requires_external_recognition")
        if self.status == "ACCREDITED":
            if not self.externally_recognised or self.evidence_class not in {"A", "B"}:
                raise ValueError("accreditation_requires_external_primary_evidence")
            if not self.issuer.strip() or not self.evidence_ref.strip():
                raise ValueError("accreditation_requires_issuer_and_reference")
        if self.diplomatic_status_claimed and self.status != "ACCREDITED":
            raise ValueError("diplomatic_claim_requires_accredited_status")


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    representative_ref: str
    permission: str
    decision: str
    scope: str
    jurisdiction: str = ""
    expires_on: str = ""
    evidence_record_id: str = ""
    founder_approved: bool = False
    revoked: bool = False
    government_authority: bool = False

    def __post_init__(self) -> None:
        for value, error, limit in (
            (self.representative_ref, "representative_ref_required", 160),
            (self.permission, "permission_required", 100),
            (self.scope, "authority_scope_required", 500),
        ):
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(error)
        if self.decision not in _DECISIONS:
            raise ValueError("invalid_authority_decision")
        if self.permission.strip().casefold() in _EXTERNAL_ONLY_PERMISSIONS:
            raise ValueError("external_diplomatic_authority_cannot_be_self_granted")
        if self.expires_on:
            try:
                date.fromisoformat(self.expires_on)
            except ValueError as exc:
                raise ValueError("invalid_authority_expiry") from exc
        if self.evidence_record_id:
            _record_id(self.evidence_record_id)
        if self.government_authority:
            raise ValueError("oap_cannot_self_grant_government_authority")


@dataclass(frozen=True, slots=True)
class MissionRecord:
    title: str
    purpose: str
    status: str = "DRAFT"
    evidence_record_id: str = ""
    authority_record_id: str = ""
    outcome: str = ""
    archived: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip() or len(self.title) > 160:
            raise ValueError("mission_title_required")
        if not isinstance(self.purpose, str) or not self.purpose.strip() or len(self.purpose) > 1000:
            raise ValueError("mission_purpose_required")
        if self.status not in {"DRAFT", "REVIEW", "APPROVED", "ACTIVE", "COMPLETE", "BLOCKED"}:
            raise ValueError("invalid_mission_status")
        if self.evidence_record_id:
            _record_id(self.evidence_record_id)
        if self.authority_record_id:
            _record_id(self.authority_record_id)


@dataclass(frozen=True, slots=True)
class CredentialRecord:
    holder_ref: str
    role_label: str
    authority_record_id: str
    status: str = "ACTIVE"
    expires_on: str = ""
    public_claim: str = "OAP internal representative credential"
    government_credential: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.holder_ref, str) or not self.holder_ref.strip():
            raise ValueError("credential_holder_required")
        if not isinstance(self.role_label, str) or not self.role_label.strip() or len(self.role_label) > 120:
            raise ValueError("credential_role_required")
        _record_id(self.authority_record_id)
        if self.status not in {"ACTIVE", "EXPIRED", "REVOKED", "BLOCKED"}:
            raise ValueError("invalid_credential_status")
        if self.expires_on:
            try:
                date.fromisoformat(self.expires_on)
            except ValueError as exc:
                raise ValueError("invalid_credential_expiry") from exc
        if self.government_credential:
            raise ValueError("oap_cannot_issue_government_credential")
        lowered = self.role_label.casefold()
        if any(term in lowered for term in ("diplomat", "ambassador", "consul", "embassy")):
            raise ValueError("credential_role_must_not_imply_external_diplomatic_status")


def _history(owner_id: str, record_type: str, record_id: str) -> list[dict[str, Any]]:
    rows = workspaces.list_global_affairs_records(
        owner_id, record_type=record_type, record_id=record_id, limit=_LIMIT,
    )
    receipts = workspaces.list_global_affairs_audit_receipts(
        owner_id, record_type=record_type, record_id=record_id, limit=_LIMIT,
    )
    if len(rows) >= _LIMIT or len(receipts) >= _LIMIT:
        raise GlobalAffairsUnavailable("global_affairs_history_limit_reached")
    if len(rows) != len(receipts):
        raise GlobalAffairsUnavailable("global_affairs_record_receipt_count_mismatch")
    receipt_by_version: dict[int, dict[str, Any]] = {}
    for receipt in receipts:
        metadata = receipt.get("metadata")
        version = metadata.get("version") if isinstance(metadata, dict) else None
        if type(version) is not int or version in receipt_by_version:
            raise GlobalAffairsUnavailable("global_affairs_audit_receipt_invalid")
        receipt_by_version[version] = receipt

    versions: list[dict[str, Any]] = []
    for row in rows:
        try:
            entry = json.loads(row["body"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GlobalAffairsUnavailable("global_affairs_history_unreadable") from exc
        version = entry.get("version")
        receipt = receipt_by_version.get(version) if type(version) is int else None
        metadata = receipt.get("metadata") if receipt else None
        if (
            not isinstance(entry, dict)
            or entry.get("owner_id") != owner_id
            or entry.get("record_type") != record_type
            or entry.get("record_id") != record_id
            or row.get("title") != f"{_PREFIX}{record_type}:{record_id}:v{version}"
            or row.get("status") != "draft"
            or not isinstance(metadata, dict)
            or receipt.get("actor_id") != owner_id
            or receipt.get("target") != f"global_affairs:{record_type}:{record_id}"
            or metadata.get("record_id") != row.get("record_id")
            or metadata.get("digest") != entry.get("digest")
            or metadata.get("external_legal_status_conferred") is not False
        ):
            raise GlobalAffairsUnavailable("global_affairs_scope_or_receipt_mismatch")
        versions.append(entry)

    versions.sort(key=lambda item: item.get("version", 0))
    previous = "GENESIS"
    for index, entry in enumerate(versions, 1):
        payload = {key: value for key, value in entry.items() if key != "digest"}
        if (
            entry.get("version") != index
            or entry.get("previous_hash") != previous
            or entry.get("digest") != _digest(payload)
            or entry.get("external_legal_status_conferred") is not False
        ):
            raise GlobalAffairsUnavailable("global_affairs_history_tampered_or_forked")
        previous = str(entry["digest"])
    return versions


def get(owner_id: object, *, record_type: str, record_id: object) -> dict[str, Any]:
    owner = _owner(owner_id)
    rid = _record_id(record_id)
    if record_type not in _RECORD_TYPES:
        raise ValueError("invalid_global_affairs_record_type")
    versions = _history(owner, record_type, rid)
    if not versions:
        raise GlobalAffairsUnavailable("global_affairs_record_not_found")
    latest = versions[-1]
    return {
        "record_type": record_type,
        "record_id": rid,
        "version": latest["version"],
        "digest": latest["digest"],
        "data": latest["data"],
        "audit_readback_verified": True,
        "external_legal_status_conferred": False,
    }


def _append(
    owner_id: object,
    *,
    record_type: str,
    record_id: object,
    data: dict[str, Any],
    expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, Any]:
    if type(stopped) is not bool or stopped:
        raise PermissionError("STOP: global affairs write blocked")
    owner = _owner(owner_id)
    rid = _record_id(record_id)
    if record_type not in _RECORD_TYPES:
        raise ValueError("invalid_global_affairs_record_type")
    versions = _history(owner, record_type, rid)
    previous = str(versions[-1]["digest"]) if versions else "GENESIS"
    required_hash = previous if versions else ""
    if expected_last_hash != required_hash:
        raise GlobalAffairsUnavailable("stale_global_affairs_version")
    if versions and versions[-1].get("data") == data:
        return {**get(owner, record_type=record_type, record_id=rid), "changed": False}

    version = len(versions) + 1
    payload = {
        "owner_id": owner,
        "record_type": record_type,
        "record_id": rid,
        "version": version,
        "previous_hash": previous,
        "data": data,
        "external_legal_status_conferred": False,
    }
    entry = {**payload, "digest": _digest(payload)}
    body = json.dumps(entry, sort_keys=True, separators=(",", ":"), allow_nan=False)
    workspaces.add_global_affairs_record_atomic(
        owner,
        record_type=record_type,
        record_id=rid,
        version=version,
        digest=str(entry["digest"]),
        title=f"{_PREFIX}{record_type}:{rid}:v{version}",
        body=body,
    )
    saved = get(owner, record_type=record_type, record_id=rid)
    if saved["digest"] != entry["digest"] or saved["version"] != version:
        raise GlobalAffairsUnavailable("global_affairs_write_readback_mismatch")
    return {**saved, "changed": True}


def save_evidence(
    owner_id: object,
    record_id: object,
    evidence: EvidenceRecord,
    *,
    expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, Any]:
    if not isinstance(evidence, EvidenceRecord):
        raise TypeError("typed_global_affairs_evidence_required")
    return _append(
        owner_id,
        record_type="evidence",
        record_id=record_id,
        data=asdict(evidence),
        expected_last_hash=expected_last_hash,
        stopped=stopped,
    )


def save_authority(
    owner_id: object,
    record_id: object,
    grant: AuthorityGrant,
    *,
    expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, Any]:
    if not isinstance(grant, AuthorityGrant):
        raise TypeError("typed_global_affairs_authority_required")
    return _append(
        owner_id,
        record_type="authority",
        record_id=record_id,
        data=asdict(grant),
        expected_last_hash=expected_last_hash,
        stopped=stopped,
    )


def assess_authority(
    owner_id: object,
    record_id: object,
    *,
    on_date: date | None = None,
) -> dict[str, Any]:
    value = get(owner_id, record_type="authority", record_id=record_id)
    grant = AuthorityGrant(**value["data"])
    today = on_date or datetime.now(UTC).date()
    if grant.revoked:
        return {"decision": "BLOCK", "reason": "authority_revoked", "record": value}
    if grant.expires_on and date.fromisoformat(grant.expires_on) < today:
        return {"decision": "BLOCK", "reason": "authority_expired", "record": value}
    if grant.decision == "ALLOW" and not grant.founder_approved:
        return {"decision": "REVIEW", "reason": "founder_approval_required", "record": value}
    return {"decision": grant.decision, "reason": "authority_matrix", "record": value}



def save_mission(
    owner_id: object,
    record_id: object,
    mission: MissionRecord,
    *,
    expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, Any]:
    if not isinstance(mission, MissionRecord):
        raise TypeError("typed_global_affairs_mission_required")
    if mission.status in {"APPROVED", "ACTIVE", "COMPLETE"}:
        if not mission.evidence_record_id or not mission.authority_record_id:
            raise ValueError("mission_requires_evidence_and_authority")
        evidence = get(owner_id, record_type="evidence", record_id=mission.evidence_record_id)
        authority = assess_authority(owner_id, mission.authority_record_id)
        if evidence["data"].get("status") in {"DRAFT", "UNVERIFIED", "BLOCKED", "REVOKED", "EXPIRED"}:
            raise ValueError("mission_evidence_not_usable")
        if authority["decision"] != "ALLOW":
            raise ValueError("mission_authority_not_allowed")
    return _append(
        owner_id,
        record_type="mission",
        record_id=record_id,
        data=asdict(mission),
        expected_last_hash=expected_last_hash,
        stopped=stopped,
    )


def save_credential(
    owner_id: object,
    record_id: object,
    credential: CredentialRecord,
    *,
    expected_last_hash: str = "",
    stopped: bool = False,
) -> dict[str, Any]:
    if not isinstance(credential, CredentialRecord):
        raise TypeError("typed_global_affairs_credential_required")
    authority = assess_authority(owner_id, credential.authority_record_id)
    if credential.status == "ACTIVE" and authority["decision"] != "ALLOW":
        raise ValueError("credential_requires_active_authority")
    return _append(
        owner_id,
        record_type="credential",
        record_id=record_id,
        data=asdict(credential),
        expected_last_hash=expected_last_hash,
        stopped=stopped,
    )


def verify_credential(
    owner_id: object,
    record_id: object,
    *,
    on_date: date | None = None,
) -> dict[str, Any]:
    value = get(owner_id, record_type="credential", record_id=record_id)
    credential = CredentialRecord(**value["data"])
    today = on_date or datetime.now(UTC).date()
    if credential.status in {"REVOKED", "BLOCKED"}:
        return {"valid": False, "reason": f"credential_{credential.status.casefold()}", "credential": value}
    if credential.expires_on and date.fromisoformat(credential.expires_on) < today:
        return {"valid": False, "reason": "credential_expired", "credential": value}
    authority = assess_authority(owner_id, credential.authority_record_id, on_date=today)
    if authority["decision"] != "ALLOW":
        return {"valid": False, "reason": f"authority_{authority['reason']}", "credential": value}
    return {
        "valid": True,
        "reason": "internal_oap_credential_valid",
        "holder_ref": credential.holder_ref,
        "role_label": credential.role_label,
        "public_claim": credential.public_claim,
        "external_legal_status_conferred": False,
    }


def recovery_readback(
    owner_id: object,
    *,
    authority_record_id: object,
    credential_record_id: object | None = None,
    on_date: date | None = None,
) -> dict[str, Any]:
    """Fail-closed recovery read-back; never resurrects revoked/expired authority."""
    authority = assess_authority(owner_id, authority_record_id, on_date=on_date)
    result: dict[str, Any] = {
        "authority_decision": authority["decision"],
        "authority_reason": authority["reason"],
        "revoked_or_expired_preserved": authority["decision"] == "BLOCK"
        and authority["reason"] in {"authority_revoked", "authority_expired"},
        "external_legal_status_conferred": False,
    }
    if credential_record_id is not None:
        credential = verify_credential(owner_id, credential_record_id, on_date=on_date)
        result["credential_valid"] = credential["valid"]
        result["credential_reason"] = credential["reason"]
        if result["revoked_or_expired_preserved"] and credential["valid"]:
            raise GlobalAffairsUnavailable("recovery_resurrected_blocked_authority")
    return result
