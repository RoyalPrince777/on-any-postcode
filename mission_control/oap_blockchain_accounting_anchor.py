"""OAP Blockchain-style accounting integrity anchor.

Creates deterministic tamper-evident hashes for SIKA journal and reconciliation
evidence. This is an integrity chain only: no token, mining, cryptocurrency,
consensus network, settlement execution or money movement.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import sika_double_entry, sika_runtime_reconciliation


class AnchorError(ValueError):
    """Raised when accounting integrity evidence is invalid."""


def _required(value: object, *, error: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AnchorError(error)
    return text


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class AccountingAnchor:
    anchor_id: str
    jurisdiction: str
    domain: str
    subject_reference: str
    previous_hash: str
    evidence_hash: str
    current_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "jurisdiction": self.jurisdiction,
            "domain": self.domain,
            "subject_reference": self.subject_reference,
            "previous_hash": self.previous_hash,
            "evidence_hash": self.evidence_hash,
            "current_hash": self.current_hash,
        }


def journal_evidence_hash(journal: sika_double_entry.JournalBatch) -> str:
    payload = journal.as_dict()
    return hashlib.sha256(_canonical_json(payload).encode()).hexdigest()


def reconciliation_evidence_hash(
    reconciliation: sika_runtime_reconciliation.ReconciliationResult,
) -> str:
    return hashlib.sha256(
        _canonical_json(reconciliation.as_dict()).encode()
    ).hexdigest()


def anchor(
    *,
    anchor_id: object,
    jurisdiction: object,
    domain: object,
    subject_reference: object,
    previous_hash: object,
    evidence_hash: object,
) -> AccountingAnchor:
    anchor_id_value = _required(anchor_id, error="anchor_id_required")
    jurisdiction_value = _required(jurisdiction, error="anchor_jurisdiction_required")
    domain_value = _required(domain, error="anchor_domain_required").upper()
    if domain_value not in {"JOURNAL", "RECONCILIATION", "SETTLEMENT"}:
        raise AnchorError("anchor_domain_invalid")

    subject = _required(subject_reference, error="anchor_subject_required")
    prev = _required(previous_hash, error="anchor_previous_hash_required")
    evidence = _required(evidence_hash, error="anchor_evidence_hash_required")

    if len(prev) != 64 or any(ch not in "0123456789abcdef" for ch in prev.lower()):
        raise AnchorError("anchor_previous_hash_invalid")
    if len(evidence) != 64 or any(
        ch not in "0123456789abcdef" for ch in evidence.lower()
    ):
        raise AnchorError("anchor_evidence_hash_invalid")

    canonical = _canonical_json(
        {
            "anchor_id": anchor_id_value,
            "jurisdiction": jurisdiction_value,
            "domain": domain_value,
            "subject_reference": subject,
            "previous_hash": prev.lower(),
            "evidence_hash": evidence.lower(),
        }
    )
    current = hashlib.sha256(canonical.encode()).hexdigest()

    return AccountingAnchor(
        anchor_id=anchor_id_value,
        jurisdiction=jurisdiction_value,
        domain=domain_value,
        subject_reference=subject,
        previous_hash=prev.lower(),
        evidence_hash=evidence.lower(),
        current_hash=current,
    )


def verify(anchor_record: AccountingAnchor) -> bool:
    rebuilt = anchor(
        anchor_id=anchor_record.anchor_id,
        jurisdiction=anchor_record.jurisdiction,
        domain=anchor_record.domain,
        subject_reference=anchor_record.subject_reference,
        previous_hash=anchor_record.previous_hash,
        evidence_hash=anchor_record.evidence_hash,
    )
    return rebuilt.current_hash == anchor_record.current_hash


def status() -> dict[str, object]:
    return {
        "system": "OAP Blockchain Accounting Anchor",
        "first_party": True,
        "mode": "tamper_evident_integrity_chain",
        "journal_anchor": True,
        "reconciliation_anchor": True,
        "jurisdiction_namespaced": True,
        "cryptocurrency": False,
        "token_issued": False,
        "mining": False,
        "settlement_execution": False,
        "money_movement": False,
        "human_authority_final": True,
    }
