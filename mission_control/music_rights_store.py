"""Persistent first-party OAP Music rights grants.

This registry persists scoped grant records and revocations for canonical Music
assets. It deliberately does not let a creator self-certify grantor authority or
human approval. Those trusted booleans remain false until a separately governed
review adapter supplies independently verified receipts.

The registry feeds the shared rights_core evaluator and never enables playback,
publishing, distribution, payment, or SIKA by itself.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from . import postgres_db, rights_core

MUSIC_RIGHTS_MIGRATION_VERSION = "0014_oap_music_rights_grants"

SCHEMA_STATEMENTS = (
    """ALTER TABLE oap_music_assets
       ADD COLUMN IF NOT EXISTS stopped BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE oap_music_assets
       ADD COLUMN IF NOT EXISTS stopped_at TIMESTAMPTZ""",
    """CREATE TABLE IF NOT EXISTS oap_music_rights_grants (
        grant_id UUID PRIMARY KEY,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        release_id UUID NOT NULL REFERENCES oap_music_releases(release_id) ON DELETE CASCADE,
        asset_id UUID NOT NULL REFERENCES oap_music_assets(asset_id) ON DELETE CASCADE,
        grantor_reference TEXT NOT NULL,
        right_type TEXT NOT NULL,
        permitted_uses TEXT[] NOT NULL,
        territories TEXT[] NOT NULL,
        permitted_channels TEXT[] NOT NULL,
        valid_from TIMESTAMPTZ,
        valid_until TIMESTAMPTZ,
        derivatives_allowed BOOLEAN NOT NULL DEFAULT FALSE,
        commercial_use_allowed BOOLEAN NOT NULL DEFAULT FALSE,
        attribution_required BOOLEAN NOT NULL DEFAULT FALSE,
        evidence_hashes TEXT[] NOT NULL,
        authority_verified BOOLEAN NOT NULL DEFAULT FALSE,
        authority_receipt_hash CHAR(64),
        human_approved BOOLEAN NOT NULL DEFAULT FALSE,
        human_approval_receipt_hash CHAR(64),
        revoked BOOLEAN NOT NULL DEFAULT FALSE,
        revocation_receipt_hash CHAR(64),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMPTZ,
        CHECK (cardinality(permitted_uses) > 0),
        CHECK (cardinality(territories) > 0),
        CHECK (cardinality(permitted_channels) > 0),
        CHECK (cardinality(evidence_hashes) > 0),
        CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_rights_asset_created
       ON oap_music_rights_grants(owner_identity_id,asset_id,created_at,grant_id)""",
    """CREATE INDEX IF NOT EXISTS ix_music_rights_release_created
       ON oap_music_rights_grants(owner_identity_id,release_id,created_at,grant_id)""",
    """CREATE TABLE IF NOT EXISTS oap_music_rights_review_receipts (
        receipt_id UUID PRIMARY KEY,
        grant_id UUID NOT NULL REFERENCES oap_music_rights_grants(grant_id) ON DELETE CASCADE,
        asset_id UUID NOT NULL REFERENCES oap_music_assets(asset_id) ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        reviewer_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        review_kind TEXT NOT NULL CHECK (review_kind IN ('AUTHORITY','HUMAN_APPROVAL')),
        evidence_hashes TEXT[] NOT NULL,
        decision TEXT NOT NULL CHECK (decision IN ('APPROVE','REJECT')),
        receipt_hash CHAR(64) NOT NULL UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (cardinality(evidence_hashes) > 0)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_rights_review_grant_created
       ON oap_music_rights_review_receipts(grant_id,created_at,receipt_id)""",
)


class MusicRightsUnavailable(RuntimeError):
    pass


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _instant(value: object, name: str, *, optional: bool = True) -> str | None:
    if value in (None, "") and optional:
        return None
    if not isinstance(value, str):
        raise TypeError(f"invalid_{name}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid_{name}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"invalid_{name}")
    return parsed.astimezone(timezone.utc).isoformat()


def _draft_grant(
    *,
    grant_id: str,
    asset_id: str,
    owner_identity_id: str,
    grantor_reference: object,
    right_type: object,
    permitted_uses: object,
    territories: object,
    permitted_channels: object,
    evidence_hashes: object,
    valid_from: object = None,
    valid_until: object = None,
    derivatives_allowed: bool = False,
    commercial_use_allowed: bool = False,
    attribution_required: bool = False,
) -> dict[str, object]:
    """Canonicalize a persisted grant while forcing trust gates to REVIEW."""
    candidate = {
        "grant_id": grant_id,
        "asset_id": asset_id,
        "owner_identity_id": owner_identity_id,
        "grantor_reference": grantor_reference,
        "right_type": right_type,
        "permitted_uses": permitted_uses,
        "territories": territories,
        "permitted_channels": permitted_channels,
        "valid_from": _instant(valid_from, "valid_from"),
        "valid_until": _instant(valid_until, "valid_until"),
        "derivatives_allowed": bool(derivatives_allowed),
        "commercial_use_allowed": bool(commercial_use_allowed),
        "attribution_required": bool(attribution_required),
        "evidence_hashes": evidence_hashes,
        "authority_verified": False,
        "authority_receipt_hash": None,
        "human_approved": False,
        "human_approval_receipt_hash": None,
        "revoked": False,
        "revocation_receipt_hash": None,
    }
    return rights_core.canonical_grant(candidate)


def _row_to_grant(row: object) -> dict[str, object]:
    return {
        "grant_id": str(row[0]),
        "asset_id": str(row[1]),
        "owner_identity_id": str(row[2]),
        "grantor_reference": str(row[3]),
        "right_type": str(row[4]),
        "permitted_uses": list(row[5]),
        "territories": list(row[6]),
        "permitted_channels": list(row[7]),
        "valid_from": row[8].isoformat() if row[8] else None,
        "valid_until": row[9].isoformat() if row[9] else None,
        "derivatives_allowed": bool(row[10]),
        "commercial_use_allowed": bool(row[11]),
        "attribution_required": bool(row[12]),
        "evidence_hashes": list(row[13]),
        "authority_verified": bool(row[14]),
        "authority_receipt_hash": str(row[15]) if row[15] else None,
        "human_approved": bool(row[16]),
        "human_approval_receipt_hash": str(row[17]) if row[17] else None,
        "revoked": bool(row[18]),
        "revocation_receipt_hash": str(row[19]) if row[19] else None,
    }



def _review_receipt_payload(
    *,
    receipt_id: str,
    grant_id: str,
    asset_id: str,
    owner_identity_id: str,
    reviewer_identity_id: str,
    review_kind: str,
    evidence_hashes: list[str],
    decision: str,
) -> dict[str, object]:
    return {
        "receipt_id": receipt_id,
        "grant_id": grant_id,
        "asset_id": asset_id,
        "owner_identity_id": owner_identity_id,
        "reviewer_identity_id": reviewer_identity_id,
        "review_kind": review_kind,
        "evidence_hashes": sorted(evidence_hashes),
        "decision": decision,
        "authority_transferred": False,
        "playback_authorized": False,
        "public_catalogue_enabled": False,
        "human_authority_final": True,
    }


def _review_receipt_hash(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class MusicRightsStore:
    def create_review_grant(
        self,
        *,
        owner_identity_id: object,
        release_id: object,
        asset_id: object,
        grantor_reference: object,
        right_type: object,
        permitted_uses: object,
        territories: object,
        permitted_channels: object,
        evidence_hashes: object,
        valid_from: object = None,
        valid_until: object = None,
        derivatives_allowed: bool = False,
        commercial_use_allowed: bool = False,
        attribution_required: bool = False,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        release = _uuid(release_id, "release_id")
        asset = _uuid(asset_id, "asset_id")
        grant_id = str(uuid4())
        grant = _draft_grant(
            grant_id=grant_id,
            asset_id=asset,
            owner_identity_id=owner,
            grantor_reference=grantor_reference,
            right_type=right_type,
            permitted_uses=permitted_uses,
            territories=territories,
            permitted_channels=permitted_channels,
            evidence_hashes=evidence_hashes,
            valid_from=valid_from,
            valid_until=valid_until,
            derivatives_allowed=derivatives_allowed,
            commercial_use_allowed=commercial_use_allowed,
            attribution_required=attribution_required,
        )
        try:
            with postgres_db.connect() as connection:
                owned = connection.execute(
                    """SELECT 1 FROM oap_music_assets
                       WHERE asset_id=%s AND release_id=%s AND owner_identity_id=%s
                       FOR UPDATE""",
                    (asset, release, owner),
                ).fetchone()
                if owned is None:
                    raise PermissionError("music_asset_not_owned")
                receipt_rows = connection.execute(
                    """SELECT evidence_sha256 FROM oap_music_evidence_receipts
                       WHERE owner_identity_id=%s AND release_id=%s""",
                    (owner, release),
                ).fetchall()
                known = {str(row[0]) for row in receipt_rows}
                supplied = set(grant["evidence_hashes"])
                if not supplied.issubset(known):
                    raise PermissionError("rights_evidence_not_owned")
                connection.execute(
                    """INSERT INTO oap_music_rights_grants(
                       grant_id,owner_identity_id,release_id,asset_id,grantor_reference,
                       right_type,permitted_uses,territories,permitted_channels,
                       valid_from,valid_until,derivatives_allowed,commercial_use_allowed,
                       attribution_required,evidence_hashes,authority_verified,
                       human_approved,revoked)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,FALSE,FALSE,FALSE)""",
                    (
                        grant_id, owner, release, asset, grant["grantor_reference"],
                        grant["right_type"], list(grant["permitted_uses"]),
                        list(grant["territories"]), list(grant["permitted_channels"]),
                        grant["valid_from"], grant["valid_until"],
                        grant["derivatives_allowed"], grant["commercial_use_allowed"],
                        grant["attribution_required"], list(grant["evidence_hashes"]),
                    ),
                )
                connection.commit()
        except (PermissionError, TypeError, ValueError):
            raise
        except Exception as exc:
            raise MusicRightsUnavailable("music_rights_store_failed") from exc
        return {
            **grant,
            "release_id": release,
            "review_state": "REVIEW_REQUIRED",
            "playback_authorized": False,
            "public_catalogue_enabled": False,
        }

    def record_authority_review(
        self,
        *,
        owner_identity_id: object,
        grant_id: object,
        reviewer_identity_id: object,
        evidence_hashes: object,
        approved: bool,
    ) -> dict[str, object]:
        return self._record_review(
            owner_identity_id=owner_identity_id,
            grant_id=grant_id,
            reviewer_identity_id=reviewer_identity_id,
            evidence_hashes=evidence_hashes,
            review_kind="AUTHORITY",
            approved=approved,
        )

    def record_human_approval(
        self,
        *,
        owner_identity_id: object,
        grant_id: object,
        reviewer_identity_id: object,
        evidence_hashes: object,
        approved: bool,
    ) -> dict[str, object]:
        return self._record_review(
            owner_identity_id=owner_identity_id,
            grant_id=grant_id,
            reviewer_identity_id=reviewer_identity_id,
            evidence_hashes=evidence_hashes,
            review_kind="HUMAN_APPROVAL",
            approved=approved,
        )

    def _record_review(
        self,
        *,
        owner_identity_id: object,
        grant_id: object,
        reviewer_identity_id: object,
        evidence_hashes: object,
        review_kind: str,
        approved: bool,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        gid = _uuid(grant_id, "grant_id")
        reviewer = _uuid(reviewer_identity_id, "reviewer_identity_id")
        if reviewer == owner:
            raise PermissionError("independent_reviewer_required")
        if not isinstance(evidence_hashes, (list, tuple, set, frozenset)):
            raise TypeError("invalid_review_evidence_hashes")
        evidence = sorted({
            rights_core._sha256(value, "review_evidence_hash")
            for value in evidence_hashes
        })
        if not evidence:
            raise ValueError("missing_review_evidence")
        if review_kind not in {"AUTHORITY", "HUMAN_APPROVAL"}:
            raise ValueError("invalid_review_kind")
        decision = "APPROVE" if approved else "REJECT"
        receipt_id = str(uuid4())
        try:
            with postgres_db.connect() as connection:
                grant = connection.execute(
                    """SELECT asset_id,release_id FROM oap_music_rights_grants
                       WHERE grant_id=%s AND owner_identity_id=%s
                       FOR UPDATE""",
                    (gid, owner),
                ).fetchone()
                if grant is None:
                    raise PermissionError("music_grant_not_owned")
                asset = str(grant[0])
                release = str(grant[1])
                known_rows = connection.execute(
                    """SELECT evidence_sha256 FROM oap_music_evidence_receipts
                       WHERE owner_identity_id=%s AND release_id=%s""",
                    (owner, release),
                ).fetchall()
                known = {str(row[0]) for row in known_rows}
                if not set(evidence).issubset(known):
                    raise PermissionError("review_evidence_not_owned")
                payload = _review_receipt_payload(
                    receipt_id=receipt_id,
                    grant_id=gid,
                    asset_id=asset,
                    owner_identity_id=owner,
                    reviewer_identity_id=reviewer,
                    review_kind=review_kind,
                    evidence_hashes=evidence,
                    decision=decision,
                )
                receipt_hash = _review_receipt_hash(payload)
                connection.execute(
                    """INSERT INTO oap_music_rights_review_receipts(
                       receipt_id,grant_id,asset_id,owner_identity_id,
                       reviewer_identity_id,review_kind,evidence_hashes,
                       decision,receipt_hash)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        receipt_id, gid, asset, owner, reviewer, review_kind,
                        evidence, decision, receipt_hash,
                    ),
                )
                if review_kind == "AUTHORITY":
                    connection.execute(
                        """UPDATE oap_music_rights_grants
                           SET authority_verified=%s,
                               authority_receipt_hash=%s
                           WHERE grant_id=%s AND owner_identity_id=%s""",
                        (
                            bool(approved),
                            receipt_hash if approved else None,
                            gid,
                            owner,
                        ),
                    )
                else:
                    connection.execute(
                        """UPDATE oap_music_rights_grants
                           SET human_approved=%s,
                               human_approval_receipt_hash=%s
                           WHERE grant_id=%s AND owner_identity_id=%s""",
                        (
                            bool(approved),
                            receipt_hash if approved else None,
                            gid,
                            owner,
                        ),
                    )
                connection.commit()
        except (PermissionError, TypeError, ValueError):
            raise
        except Exception as exc:
            raise MusicRightsUnavailable("music_rights_review_failed") from exc
        return {
            **payload,
            "receipt_hash": receipt_hash,
            "rights_verified_by_software": False,
            "legal_validity_verified": False,
            "media_delivery_performed": False,
        }

    def list_for_asset(
        self, *, owner_identity_id: object, asset_id: object
    ) -> list[dict[str, object]]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        asset = _uuid(asset_id, "asset_id")
        try:
            with postgres_db.connect(readonly=True) as connection:
                rows = connection.execute(
                    """SELECT grant_id,asset_id,owner_identity_id,grantor_reference,
                              right_type,permitted_uses,territories,permitted_channels,
                              valid_from,valid_until,derivatives_allowed,
                              commercial_use_allowed,attribution_required,evidence_hashes,
                              authority_verified,authority_receipt_hash,human_approved,
                              human_approval_receipt_hash,revoked,revocation_receipt_hash
                       FROM oap_music_rights_grants
                       WHERE owner_identity_id=%s AND asset_id=%s
                       ORDER BY created_at,grant_id""",
                    (owner, asset),
                ).fetchall()
        except Exception as exc:
            raise MusicRightsUnavailable("music_rights_read_failed") from exc
        return [_row_to_grant(row) for row in rows]

    def evaluate_platform_use(
        self,
        *,
        owner_identity_id: object,
        asset_id: object,
        use: object,
        territory: object,
        channel: object = "OAP Music",
        requested_at: object = None,
    ) -> dict[str, object]:
        """Evaluate persisted rights for an OAP platform use; never deliver media."""
        owner = _uuid(owner_identity_id, "owner_identity_id")
        asset = _uuid(asset_id, "asset_id")
        when = (
            datetime.now(timezone.utc).isoformat()
            if requested_at in (None, "")
            else _instant(requested_at, "requested_at", optional=False)
        )
        try:
            with postgres_db.connect(readonly=True) as connection:
                row = connection.execute(
                    """SELECT release_id,sha256 FROM oap_music_assets
                       WHERE asset_id=%s AND owner_identity_id=%s""",
                    (asset, owner),
                ).fetchone()
                if row is None:
                    raise PermissionError("music_asset_not_owned")
                grants = connection.execute(
                    """SELECT grant_id,asset_id,owner_identity_id,grantor_reference,
                              right_type,permitted_uses,territories,permitted_channels,
                              valid_from,valid_until,derivatives_allowed,
                              commercial_use_allowed,attribution_required,evidence_hashes,
                              authority_verified,authority_receipt_hash,human_approved,
                              human_approval_receipt_hash,revoked,revocation_receipt_hash
                       FROM oap_music_rights_grants
                       WHERE owner_identity_id=%s AND asset_id=%s
                       ORDER BY created_at,grant_id""",
                    (owner, asset),
                ).fetchall()
        except PermissionError:
            raise
        except Exception as exc:
            raise MusicRightsUnavailable("music_rights_evaluation_failed") from exc
        decision = rights_core.evaluate_use(
            asset={
                "asset_id": asset,
                "owner_identity_id": owner,
                "kind": "audio",
                "content_sha256": str(row[1]),
                "parent_asset_id": None,
                "source_reference": f"oap:music:{row[0]}",
            },
            grants=[_row_to_grant(item) for item in grants],
            request={
                "asset_id": asset,
                "requester_identity_id": owner,
                "use": use,
                "territory": territory,
                "channel": channel,
                "requested_at": when,
                "derivative": False,
            },
        )
        return {
            "release_id": str(row[0]),
            "asset_id": asset,
            "decision": decision,
            "platform_use_only": True,
            "listener_entitlement_checked": False,
            "media_integrity_bound_to_asset_sha256": True,
            "media_delivery_performed": False,
            "public_catalogue_enabled": False,
            "human_authority_final": True,
        }

    def revoke(
        self,
        *,
        owner_identity_id: object,
        grant_id: object,
        revocation_receipt_hash: object,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        gid = _uuid(grant_id, "grant_id")
        receipt = rights_core._sha256(
            revocation_receipt_hash, "revocation_receipt_hash"
        )
        try:
            with postgres_db.connect() as connection:
                row = connection.execute(
                    """UPDATE oap_music_rights_grants
                       SET revoked=TRUE,revocation_receipt_hash=%s,
                           revoked_at=COALESCE(revoked_at,CURRENT_TIMESTAMP)
                       WHERE grant_id=%s AND owner_identity_id=%s
                       RETURNING asset_id""",
                    (receipt, gid, owner),
                ).fetchone()
                connection.commit()
        except Exception as exc:
            raise MusicRightsUnavailable("music_rights_revoke_failed") from exc
        if row is None:
            raise PermissionError("music_grant_not_owned")
        return {
            "grant_id": gid,
            "asset_id": str(row[0]),
            "revoked": True,
            "revocation_receipt_hash": receipt,
            "playback_authorized": False,
            "public_catalogue_enabled": False,
            "human_authority_final": True,
        }
