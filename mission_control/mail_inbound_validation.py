"""Fail-closed RFC 5322 message validation for future OAP-owned inbound transport.

No SMTP listener, authentication bypass, database writes, or delivery claim.
The trusted transport must resolve the envelope recipient to a Founder owner
before calling this parser. Never trust message To headers for routing.
"""
from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr

MAX_MESSAGE_BYTES = 256_000
MAX_SUBJECT = 200
MAX_BODY = 20_000
MAX_CORRESPONDENT = 320


class InboundMessageRejected(ValueError):
    """Inbound payload is unsafe or incompatible with mailbox limits."""


@dataclass(frozen=True)
class ParsedInboundMessage:
    subject: str
    body: str
    correspondent: str


def parse_inbound_message(raw: bytes) -> ParsedInboundMessage:
    """Parse a bounded plain-text email without accepting attachments or HTML.

    This is a preparation step, NOT an inbound mail transport. The caller must
    authenticate its source, validate the SMTP envelope recipient and provide
    durable idempotent persistence before acknowledging SMTP delivery.
    """
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_MESSAGE_BYTES:
        raise InboundMessageRejected("invalid_inbound_size")
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except (ValueError, TypeError) as exc:
        raise InboundMessageRejected("invalid_inbound_message") from exc
    if message.defects:
        raise InboundMessageRejected("invalid_inbound_headers")
    for name in ("From", "Subject"):
        if len(message.get_all(name, [])) != 1:
            raise InboundMessageRejected("invalid_inbound_headers")
    if message.is_multipart() or message.get_content_type() != "text/plain":
        raise InboundMessageRejected("unsupported_inbound_content")
    if message.get("Content-Disposition"):
        raise InboundMessageRejected("unsupported_inbound_content")
    sender = str(message["From"])
    _, address = parseaddr(sender)
    if not address or any(c in address for c in "\r\n\x00") or len(address) > MAX_CORRESPONDENT:
        raise InboundMessageRejected("invalid_inbound_sender")
    subject = str(message["Subject"])
    if len(subject) > MAX_SUBJECT or any(c in subject for c in "\r\n\x00"):
        raise InboundMessageRejected("invalid_inbound_subject")
    try:
        body = message.get_content()
    except (LookupError, UnicodeError, ValueError) as exc:
        raise InboundMessageRejected("invalid_inbound_body") from exc
    if not isinstance(body, str) or len(body) > MAX_BODY or "\x00" in body:
        raise InboundMessageRejected("invalid_inbound_body")
    return ParsedInboundMessage(subject=subject, body=body, correspondent=address)
