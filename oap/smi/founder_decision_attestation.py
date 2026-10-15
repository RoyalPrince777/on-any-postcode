"""Authenticated Founder attestations for SMI decisions (advisory, not execution).

HMAC is a bounded server-side proof when the signing key is stored securely.
This is not a public-key identity proof or a substitute for MFA, access control,
key rotation, replay prevention across services, or Founder authentication.
"""
from __future__ import annotations

import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from oap.smi.governance_decision_registry import DecisionRecord


@dataclass(frozen=True)
class FounderAttestation:
    decision_id: str
    record_hash: str
    founder_id: str
    decision: str
    issued_at: str
    expires_at: str
    signature: str


def _payload(attestation: FounderAttestation) -> bytes:
    data = {
        "decision_id": attestation.decision_id,
        "record_hash": attestation.record_hash,
        "founder_id": attestation.founder_id,
        "decision": attestation.decision,
        "issued_at": attestation.issued_at,
        "expires_at": attestation.expires_at,
    }
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def _time(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone required")
    return result.astimezone(UTC)


def sign_founder_decision(
    record: DecisionRecord,
    *,
    founder_id: str,
    decision: str,
    issued_at: datetime,
    expires_at: datetime,
    secret: bytes,
) -> FounderAttestation:
    """Only call after independent Founder authentication and key access checks."""
    if len(secret) < 32 or not founder_id.strip():
        raise ValueError("strong secret and Founder ID required")
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError("invalid Founder decision")
    if decision == "APPROVED" and record.governance_verdict != "READY_FOR_FOUNDER_REVIEW":
        raise ValueError("blocked governance cannot be approved")
    if issued_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("timezone required")
    issued = issued_at.astimezone(UTC)
    expiry = expires_at.astimezone(UTC)
    if expiry <= issued:
        raise ValueError("attestation expiry must follow issuance")
    unsigned = FounderAttestation(
        decision_id=record.decision_id, record_hash=record.record_hash,
        founder_id=founder_id.strip(), decision=decision,
        issued_at=issued.isoformat(), expires_at=expiry.isoformat(), signature="",
    )
    signature = hmac.new(secret, _payload(unsigned), sha256).hexdigest()
    return FounderAttestation(**{**unsigned.__dict__, "signature": signature})


def verify_founder_decision(
    record: DecisionRecord,
    attestation: FounderAttestation,
    *,
    expected_founder_id: str,
    now: datetime,
    secret: bytes,
) -> bool:
    """Fail closed; a valid attestation never directly authorises execution."""
    if len(secret) < 32 or now.tzinfo is None or now.utcoffset() is None:
        return False
    if (attestation.decision_id != record.decision_id
            or attestation.record_hash != record.record_hash
            or attestation.founder_id != expected_founder_id
            or attestation.decision not in ("APPROVED", "REJECTED")
            or (attestation.decision == "APPROVED"
                and record.governance_verdict != "READY_FOR_FOUNDER_REVIEW")):
        return False
    try:
        issued = _time(attestation.issued_at)
        expiry = _time(attestation.expires_at)
    except (ValueError, TypeError):
        return False
    current = now.astimezone(UTC)
    if not issued <= current < expiry:
        return False
    expected = hmac.new(secret, _payload(attestation), sha256).hexdigest()
    return hmac.compare_digest(expected, attestation.signature)
