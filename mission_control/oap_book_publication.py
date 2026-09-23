"""OAP book edition publication evidence gate; never a licence generator.

All evidence IDs are references to separately verified records. Presence here
cannot certify signatures or ownership; an authorised reviewer must verify each.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class EditionEvidence:
    book_id: str
    edition_id: str
    manuscript_sha256: str
    creator_id: str
    publisher_authority_id: str
    rights_record_id: str
    founder_approval_id: str
    rights_verified: bool = False
    manuscript_approved: bool = False
    public_release_approved: bool = False
    private: bool = False
    youth: bool = False
    safeguarding_approved: bool = False
    age_approved: bool = False
    expires_at: datetime | None = None


def publication_blocks(evidence: EditionEvidence, *, now: datetime) -> tuple[str, ...]:
    """Return all known blockers, rather than silently approving publication."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timezone_required")
    missing = tuple(
        field for field in (
            "book_id", "edition_id", "manuscript_sha256", "creator_id",
            "publisher_authority_id", "rights_record_id", "founder_approval_id",
        ) if not getattr(evidence, field).strip()
    )
    blocks = [f"missing_{field}" for field in missing]
    if evidence.private:
        blocks.append("private_edition")
    if not evidence.rights_verified:
        blocks.append("rights_unverified")
    if not evidence.manuscript_approved:
        blocks.append("manuscript_unapproved")
    if not evidence.public_release_approved:
        blocks.append("public_release_unapproved")
    if evidence.youth and not (
        evidence.safeguarding_approved and evidence.age_approved
    ):
        blocks.append("youth_checks_missing")
    if evidence.expires_at is not None:
        expiry = evidence.expires_at
        if expiry.tzinfo is None or expiry.utcoffset() is None:
            blocks.append("invalid_expiry_timezone")
        elif expiry.astimezone(timezone.utc) <= now.astimezone(timezone.utc):
            blocks.append("rights_expired")
    return tuple(blocks)
