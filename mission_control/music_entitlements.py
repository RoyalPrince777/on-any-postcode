"""First-party OAP Music public entitlement registry.

Rights permission and listener entitlement remain separate. A public entitlement
can only be persisted after the canonical persisted Music rights path returns
ALLOW for the same asset/use/territory/channel. This module does not deliver
media, capture payment, or create royalty/SIKA value.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from . import music_rights_store, postgres_db, rights_core

MUSIC_ENTITLEMENT_MIGRATION_VERSION = "0015_oap_music_entitlements"

SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_music_entitlements (
        entitlement_id UUID PRIMARY KEY,
        asset_id UUID NOT NULL REFERENCES oap_music_assets(asset_id) ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
        access_scope TEXT NOT NULL CHECK (access_scope IN ('PUBLIC_FREE')),
        territory TEXT NOT NULL,
        channel TEXT NOT NULL,
        valid_from TIMESTAMPTZ,
        valid_until TIMESTAMPTZ,
        rights_decision_hash CHAR(64) NOT NULL,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMPTZ,
        CHECK (valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from)
    )""",
    """CREATE INDEX IF NOT EXISTS ix_music_entitlement_asset_scope
       ON oap_music_entitlements(asset_id,access_scope,territory,channel,active)""",
)

class MusicEntitlementUnavailable(RuntimeError):
    pass


def _uuid(value: object, name: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _text(value: object, name: str) -> str:
    text = " ".join(str(value or "").split())
    if not text or len(text) > 240:
        raise ValueError(f"invalid_{name}")
    return text


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


MINIMUM_SONG_PRICE_MINOR = 100
SONG_CURRENCY = "GBP"


def song_price_intent(amount_minor: object = MINIMUM_SONG_PRICE_MINOR) -> dict[str, object]:
    try:
        amount = int(amount_minor)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_song_amount") from exc
    if amount < MINIMUM_SONG_PRICE_MINOR:
        raise ValueError("minimum_song_price_is_1_gbp")
    return {
        "currency": SONG_CURRENCY,
        "minimum_amount_minor": MINIMUM_SONG_PRICE_MINOR,
        "amount_minor": amount,
        "pay_more_allowed": True,
        "payment_capture_performed": False,
        "sika_execution_performed": False,
        "human_authority_final": True,
    }


class MusicEntitlementStore:
    def __init__(self) -> None:
        self._rights = music_rights_store.MusicRightsStore()

    def create_public_free(
        self,
        *,
        owner_identity_id: object,
        asset_id: object,
        territory: object,
        channel: object = "OAP Music",
        valid_from: object = None,
        valid_until: object = None,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        asset = _uuid(asset_id, "asset_id")
        territory_value = _text(territory, "territory")
        channel_value = _text(channel, "channel")
        start = _instant(valid_from, "valid_from")
        end = _instant(valid_until, "valid_until")
        decision = self._rights.evaluate_platform_use(
            owner_identity_id=owner,
            asset_id=asset,
            use="stream",
            territory=territory_value,
            channel=channel_value,
        )
        proof = rights_core.decision_proof(decision["decision"])
        if not proof["canonical_allow"]:
            raise PermissionError("canonical_rights_allow_required")
        entitlement_id = str(uuid4())
        try:
            with postgres_db.connect() as connection:
                connection.execute(
                    """INSERT INTO oap_music_entitlements(
                       entitlement_id,asset_id,owner_identity_id,access_scope,
                       territory,channel,valid_from,valid_until,
                       rights_decision_hash,active)
                       VALUES (%s,%s,%s,'PUBLIC_FREE',%s,%s,%s,%s,%s,TRUE)""",
                    (
                        entitlement_id,
                        asset,
                        owner,
                        territory_value,
                        channel_value,
                        start,
                        end,
                        decision["decision"]["decision_hash"],
                    ),
                )
                connection.commit()
        except Exception as exc:
            raise MusicEntitlementUnavailable(
                "music_entitlement_store_failed"
            ) from exc
        return {
            "entitlement_id": entitlement_id,
            "asset_id": asset,
            "access_scope": "PUBLIC_FREE",
            "territory": territory_value,
            "channel": channel_value,
            "active": True,
            "rights_decision_hash": decision["decision"]["decision_hash"],
            "payment_capture_performed": False,
            "royalty_payout_performed": False,
            "sika_execution_performed": False,
            "media_delivery_performed": False,
            "human_authority_final": True,
        }

    def public_gate(
        self,
        *,
        asset_id: object,
        territory: object,
        channel: object = "OAP Music",
        requested_at: object = None,
    ) -> dict[str, object]:
        asset = _uuid(asset_id, "asset_id")
        territory_value = _text(territory, "territory")
        channel_value = _text(channel, "channel")
        when = (
            datetime.now(timezone.utc)
            if requested_at in (None, "")
            else datetime.fromisoformat(
                _instant(requested_at, "requested_at", optional=False)
            )
        )
        try:
            with postgres_db.connect(readonly=True) as connection:
                row = connection.execute(
                    """SELECT entitlement_id,owner_identity_id,valid_from,valid_until,
                              rights_decision_hash
                       FROM oap_music_entitlements
                       WHERE asset_id=%s AND access_scope='PUBLIC_FREE'
                         AND territory IN (%s,'*') AND channel IN (%s,'*')
                         AND active=TRUE
                       ORDER BY created_at DESC LIMIT 1""",
                    (asset, territory_value, channel_value),
                ).fetchone()
                if row is None:
                    return {
                        "allowed": False,
                        "reason": "public_entitlement_missing",
                        "asset_id": asset,
                        "media_delivery_performed": False,
                    }
                stopped = connection.execute(
                    """SELECT stopped FROM oap_music_assets
                       WHERE asset_id=%s""",
                    (asset,),
                ).fetchone()
        except Exception as exc:
            raise MusicEntitlementUnavailable(
                "music_entitlement_gate_failed"
            ) from exc
        if stopped is None or bool(stopped[0]):
            return {
                "allowed": False,
                "reason": "music_asset_stopped_or_missing",
                "asset_id": asset,
                "media_delivery_performed": False,
            }
        start = row[2]
        end = row[3]
        if start is not None and when < start:
            return {
                "allowed": False,
                "reason": "entitlement_not_started",
                "asset_id": asset,
                "media_delivery_performed": False,
            }
        if end is not None and when >= end:
            return {
                "allowed": False,
                "reason": "entitlement_expired",
                "asset_id": asset,
                "media_delivery_performed": False,
            }
        current = self._rights.evaluate_platform_use(
            owner_identity_id=str(row[1]),
            asset_id=asset,
            use="stream",
            territory=territory_value,
            channel=channel_value,
            requested_at=when.isoformat(),
        )
        current_proof = rights_core.decision_proof(current["decision"])
        if not current_proof["canonical_allow"]:
            return {
                "allowed": False,
                "reason": "current_rights_not_allowed",
                "asset_id": asset,
                "media_delivery_performed": False,
            }
        return {
            "allowed": True,
            "reason": "public_free_entitlement",
            "entitlement_id": str(row[0]),
            "owner_identity_id": str(row[1]),
            "asset_id": asset,
            "rights_decision_hash": current["decision"]["decision_hash"],
            "entitlement_created_from_rights_decision_hash": str(row[4]),
            "territory": territory_value,
            "channel": channel_value,
            "media_delivery_performed": False,
            "payment_capture_performed": False,
            "human_authority_final": True,
        }

    def revoke(
        self,
        *,
        owner_identity_id: object,
        entitlement_id: object,
    ) -> dict[str, object]:
        owner = _uuid(owner_identity_id, "owner_identity_id")
        entitlement = _uuid(entitlement_id, "entitlement_id")
        try:
            with postgres_db.connect() as connection:
                row = connection.execute(
                    """UPDATE oap_music_entitlements
                       SET active=FALSE,revoked_at=COALESCE(revoked_at,CURRENT_TIMESTAMP)
                       WHERE entitlement_id=%s AND owner_identity_id=%s
                       RETURNING asset_id""",
                    (entitlement, owner),
                ).fetchone()
                connection.commit()
        except Exception as exc:
            raise MusicEntitlementUnavailable(
                "music_entitlement_revoke_failed"
            ) from exc
        if row is None:
            raise PermissionError("music_entitlement_not_owned")
        return {
            "entitlement_id": entitlement,
            "asset_id": str(row[0]),
            "active": False,
            "media_delivery_performed": False,
            "human_authority_final": True,
        }
