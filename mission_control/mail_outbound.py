"""First-party OAP Mail outbound relay adapter.

OAP Mail owns composition and policy. Delivery is permitted only through an
explicitly configured, allowlisted OAP-owned SMTP relay. Relay acceptance is
not proof of final recipient inbox delivery.
"""
from __future__ import annotations

import os
import re
import smtplib
import ssl
import uuid
from email.message import EmailMessage
from typing import Any

ADDRESS_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MAX_SUBJECT = 200
MAX_BODY = 20000
MAX_RECIPIENTS = 10


class MailUnavailable(RuntimeError):
    pass


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() == "true"


def _owned_hosts() -> frozenset[str]:
    return frozenset(
        item.strip().casefold()
        for item in os.environ.get("OAP_MAIL_OWNED_RELAY_HOSTS", "").split(",")
        if item.strip()
    )


def _relay_host() -> str:
    host = os.environ.get("OAP_MAIL_SMTP_HOST", "").strip().casefold()
    return host if host and host in _owned_hosts() else ""


def _relay_port() -> int:
    raw = os.environ.get("OAP_MAIL_SMTP_PORT", "465").strip()
    try:
        port = int(raw)
    except ValueError:
        return 0
    return port if 1 <= port <= 65535 else 0


def _sender() -> str:
    value = os.environ.get("OAP_MAIL_FROM_ADDRESS", "").strip()
    return value if ADDRESS_RE.fullmatch(value) else ""


def _username() -> str:
    return os.environ.get("OAP_MAIL_SMTP_USERNAME", "").strip()


def _password() -> str:
    return os.environ.get("OAP_MAIL_SMTP_PASSWORD", "")


def _normalise_recipients(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        raw = [item.strip() for item in value.split(",")]
    elif isinstance(value, (list, tuple)):
        raw = [str(item).strip() for item in value]
    else:
        raw = []
    recipients = tuple(item for item in raw if item)
    if not recipients or len(recipients) > MAX_RECIPIENTS:
        raise ValueError("invalid_recipients")
    if any(not ADDRESS_RE.fullmatch(item) for item in recipients):
        raise ValueError("invalid_recipient")
    return recipients


def _subject(value: object) -> str:
    subject = str(value or "").strip()
    if not subject or len(subject) > MAX_SUBJECT:
        raise ValueError("invalid_subject")
    return subject


def _body(value: object) -> str:
    body = str(value or "").strip()
    if not body or len(body) > MAX_BODY:
        raise ValueError("invalid_body")
    return body


def status() -> dict[str, Any]:
    host = _relay_host()
    port = _relay_port()
    sender = _sender()
    return {
        "product": "OAP Mail",
        "mode": "outbound_relay",
        "send_enabled": _flag("OAP_MAIL_SEND_ENABLED"),
        "relay_host_allowlisted": bool(host),
        "relay_port_valid": bool(port),
        "sender_configured": bool(sender),
        "smtp_credentials_configured": bool(_username() and _password()),
        "tls_required": True,
        "relay_configured": bool(host and port and sender and _username() and _password()),
        "recipient_delivery_proven": False,
        "truth_boundary": (
            "A successful send proves only that the configured OAP-owned SMTP relay "
            "accepted the message. It does not prove final recipient inbox delivery."
        ),
        "human_authority_final": True,
    }


def send(*, recipients: object, subject: object, body: object) -> dict[str, Any]:
    state = status()
    if state["send_enabled"] is not True:
        raise MailUnavailable("oap_mail_send_disabled")
    if state["relay_configured"] is not True:
        raise MailUnavailable("oap_mail_relay_not_configured")

    to = _normalise_recipients(recipients)
    clean_subject = _subject(subject)
    clean_body = _body(body)
    sender = _sender()
    host = _relay_host()
    port = _relay_port()

    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(to)
    message["Subject"] = clean_subject
    message["Message-ID"] = f"<{uuid.uuid4()}@{host}>"
    message.set_content(clean_body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, timeout=10, context=context) as client:
            client.login(_username(), _password())
            failures = client.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise MailUnavailable("oap_mail_relay_unavailable") from exc

    if failures:
        raise MailUnavailable("oap_mail_relay_rejected_recipient")

    return {
        "product": "OAP Mail",
        "accepted_by_relay": True,
        "recipient_count": len(to),
        "message_id": str(message["Message-ID"]),
        "recipient_delivery_proven": False,
        "final_delivery_status": "unknown_after_relay_acceptance",
        "human_authority_final": True,
    }
