"""Founder-only transactional Inbox persistence; no SMTP listener or delivery claim.

Caller MUST authenticate the first-party inbound transport and supply an
idempotency key stable across retries for the same accepted envelope.
This module never changes database schema or bypasses migration preflight.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from . import mail_migration, postgres_db
from .mail_inbound_envelope import FounderDelivery

# Deterministic UUID isolates inbound deduplication to the owner, recipient
# and authenticated transport-provided delivery key. Never use Message-ID
# alone: senders can forge it.
INBOUND_NAMESPACE = uuid.UUID("f5d59cba-9d36-493b-b7c4-71f98752d0d1")


class InboundStoreUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class InboundStoreReceipt:
    item_id: str
    inserted: bool


def _delivery_id(delivery: FounderDelivery, delivery_key: str) -> str:
    if not isinstance(delivery_key, str) or not 1 <= len(delivery_key) <= 256:
        raise ValueError("invalid_inbound_delivery_key")
    if any(ord(ch) < 33 or ord(ch) > 126 for ch in delivery_key):
        raise ValueError("invalid_inbound_delivery_key")
    digest = hashlib.sha256(
        (delivery.owner_id + "\x00" + delivery.recipient + "\x00" + delivery_key).encode()
    ).hexdigest()
    return str(uuid.uuid5(INBOUND_NAMESPACE, digest))


def persist_founder_inbox(
    delivery: FounderDelivery, *, delivery_key: str
) -> InboundStoreReceipt:
    """Commit once to the existing mailbox table before transport ACK.

    Caller is responsible for authenticating transport and validating the
    SMTP envelope via validate_founder_delivery. A retry of the same key is
    idempotent. Do not ACK an SMTP transaction on any exception.
    """
    if not isinstance(delivery, FounderDelivery):
        raise TypeError("invalid_inbound_delivery")
    item_id = _delivery_id(delivery, delivery_key)
    if not mail_migration.schema_status().get("schema_ready"):
        raise InboundStoreUnavailable("mail_schema_not_ready")
    try:
        with postgres_db.connect() as connection:
            try:
                row = connection.execute(
                    """INSERT INTO oap_mail_items
                       (id,owner_id,folder,subject,body,correspondent)
                       VALUES (%s,%s,'inbox',%s,%s,%s)
                       ON CONFLICT (id) DO NOTHING RETURNING id""",
                    (
                        item_id, delivery.owner_id, delivery.message.subject,
                        delivery.message.body, delivery.message.correspondent,
                    ),
                ).fetchone()
                connection.commit()
            except Exception:
                connection.rollback()
                raise
    except Exception as exc:
        raise InboundStoreUnavailable("inbound_store_unavailable") from exc
    return InboundStoreReceipt(item_id=item_id, inserted=row is not None)
