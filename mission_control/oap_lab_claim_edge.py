"""First-party OAP LAB Claim Edge: isolated, read-only research admission.

Extends research dossiers from oap_lab_research; does NOT create a second graph,
store, HRM receipt, authorization service, HTTP route, or truth authority.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal
from uuid import UUID

from mission_control.oap_lab_research import DOMAINS, Notebook

Verdict = Literal["under_investigation", "disputed", "unsupported", "established"]
Relation = Literal["documents", "supports", "challenges", "mentions", "contracts_with"]
_ALLOWED_RELATIONS = frozenset(("documents", "supports", "challenges", "mentions", "contracts_with"))


class ClaimEdgeBlocked(ValueError):
    """Fail closed without promoting or publishing a research claim."""


def _id(value: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ClaimEdgeBlocked("canonical_uuid_required") from exc


def _date(value: str) -> datetime:
    if not isinstance(value, str):
        raise ClaimEdgeBlocked("dated_evidence_required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ClaimEdgeBlocked("invalid_evidence_date") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ClaimEdgeBlocked("timezone_required")
    return parsed.astimezone(timezone.utc)


def _required(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 1024:
        raise ClaimEdgeBlocked(f"{label}_required")
    return value.strip()


@dataclass(frozen=True)
class Source:
    source_id: str
    original: bytes
    expected_sha256: str
    published_at: str
    retrieved_at: str
    independent_origin: str

    def __post_init__(self) -> None:
        _required(self.source_id, "source_id")
        _required(self.independent_origin, "independent_origin")
        if not isinstance(self.original, bytes) or not self.original:
            raise ClaimEdgeBlocked("original_source_bytes_required")
        if not isinstance(self.expected_sha256, str) or sha256(self.original).hexdigest() != self.expected_sha256:
            raise ClaimEdgeBlocked("source_byte_integrity_failed")
        if _date(self.published_at) > _date(self.retrieved_at):
            raise ClaimEdgeBlocked("source_chronology_invalid")


@dataclass(frozen=True)
class ClaimEdge:
    claim_id: str
    mission_id: str
    notebook_id: str
    domain: str
    claim: str
    subject: str
    relation: Relation
    object: str
    event_at: str
    classification: Verdict = "under_investigation"
    owner_id: str = ""
    private_subject: bool = False
    consent_for_research: bool = False
    redacted: bool = False
    stopped: bool = False

    def __post_init__(self) -> None:
        _id(self.claim_id)
        _id(self.mission_id)
        _id(self.owner_id)
        for name in ("notebook_id", "claim", "subject", "object"):
            _required(getattr(self, name), name)
        if self.domain not in DOMAINS or self.relation not in _ALLOWED_RELATIONS:
            raise ClaimEdgeBlocked("domain_or_relationship_not_allowlisted")
        if self.classification not in (
            "under_investigation", "disputed", "unsupported", "established"
        ):
            raise ClaimEdgeBlocked("invalid_evidence_classification")
        _date(self.event_at)
        if self.private_subject and (not self.consent_for_research or not self.redacted):
            raise ClaimEdgeBlocked("private_subject_requires_consent_and_redaction")


def admit_claim(
    edge: ClaimEdge,
    notebook: Notebook,
    sources: tuple[Source, ...],
    *,
    authenticated_owner_id: str,
    external_action: bool = False,
) -> dict[str, object]:
    """Return an immutable review projection, never a canonical truth promotion.

    Merely counting two source records cannot establish independence or truth.
    This first slice therefore reserves 'established' for a later separately
    reviewed evidence contract rather than accepting a caller's assertion.
    """
    if not isinstance(edge, ClaimEdge) or not isinstance(notebook, Notebook):
        raise ClaimEdgeBlocked("typed_claim_and_notebook_required")
    if edge.stopped:
        raise ClaimEdgeBlocked("stop_asserted")
    if external_action:
        raise ClaimEdgeBlocked("consequential_execution_forbidden")
    if _id(authenticated_owner_id) != _id(edge.owner_id):
        raise ClaimEdgeBlocked("owner_scope_mismatch")
    if edge.notebook_id != notebook.identifier or edge.domain != notebook.domain:
        raise ClaimEdgeBlocked("lab_notebook_reference_mismatch")
    if edge.classification == "established":
        raise ClaimEdgeBlocked("independent_review_required_for_established_claim")
    if not isinstance(sources, tuple) or not sources or any(
        not isinstance(source, Source) for source in sources
    ):
        raise ClaimEdgeBlocked("verified_source_required")
    source_ids = [s.source_id for s in sources]
    if len(set(source_ids)) != len(source_ids):
        raise ClaimEdgeBlocked("duplicate_source_id")
    event = _date(edge.event_at)
    if any(event > _date(s.retrieved_at) for s in sources):
        raise ClaimEdgeBlocked("future_event_at_retrieval")
    origins = {s.independent_origin for s in sources}
    receipt = {
        "claim_id": _id(edge.claim_id),
        "mission_id": _id(edge.mission_id),
        "notebook_id": edge.notebook_id,
        "domain": edge.domain,
        "relation": edge.relation,
        "classification": edge.classification,
        "source_ids": source_ids,
        "source_sha256": [s.expected_sha256 for s in sources],
        "independent_origins_claimed": len(origins),
        "independence_verified": False,
        "scientific_truth_established": False,
        "owner_scoped": True,
        "private_subject_redacted": bool(edge.private_subject),
        "review_only": True,
        "canonical_promotion_authorised": False,
        "publication_authorised": False,
        "execution_authorised": False,
    }
    receipt["receipt_sha256"] = sha256(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return receipt
