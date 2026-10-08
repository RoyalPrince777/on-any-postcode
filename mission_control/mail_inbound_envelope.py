"""Founder-only inbound envelope validation.

This module does not trust RFC 5322 To/Cc headers for delivery routing.
The transport must supply its authenticated SMTP envelope recipient and an
explicitly configured Founder mailbox address. It performs no DB writes.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from email.utils import parseaddr

from .mail_inbound_validation import (
    InboundMessageRejected,
    ParsedInboundMessage,
    parse_inbound_message,
)


@dataclass(frozen=True)
class FounderDelivery:
    owner_id: str
    recipient: str
    message: ParsedInboundMessage


def _mailbox_address(value: object) -> str:
    if not isinstance(value, str) or len(value) > 320:
        raise InboundMessageRejected("invalid_inbound_recipient")
    address = value.strip()
    if not address or any(c in address for c in "\r
\x00<> ,;"):
        raise InboundMessageRejected("invalid_inbound_recipient")
    if parseaddr(address)[1] != address or address.count("@") != 1:
        raise InboundMessageRejected("invalid_inbound_recipient")
    local, domain = address.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        raise InboundMessageRejected("invalid_inbound_recipient")
    return address.casefold()


def validate_founder_delivery(
    *,
    envelope_recipient: str,
    founder_address: str,
    founder_owner_id: str,
    raw_message: bytes,
) -> FounderDelivery:
    """Return a validated Founder-only delivery candidate, never a receipt.

    This is not an authentication mechanism. An authenticated first-party
    transport must call it and persist atomically before acknowledging mail.
    """
    recipient = _mailbox_address(envelope_recipient)
    if recipient != _mailbox_address(founder_address):
        raise InboundMessageRejected("inbound_recipient_not_authorized")
    try:
        owner = str(uuid.UUID(str(founder_owner_id)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise InboundMessageRejected("invalid_inbound_owner") from exc
    return FounderDelivery(
        owner_id=owner,
        recipient=recipient,
        message=parse_inbound_message(raw_message),
    )
