from __future__ import annotations

import smtplib

import pytest

from mission_control import mail_outbound


def _clear(monkeypatch):
    for name in (
        "OAP_MAIL_SEND_ENABLED",
        "OAP_MAIL_OWNED_RELAY_HOSTS",
        "OAP_MAIL_SMTP_HOST",
        "OAP_MAIL_SMTP_PORT",
        "OAP_MAIL_FROM_ADDRESS",
        "OAP_MAIL_SMTP_USERNAME",
        "OAP_MAIL_SMTP_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)


def _configured(monkeypatch):
    monkeypatch.setenv("OAP_MAIL_SEND_ENABLED", "true")
    monkeypatch.setenv("OAP_MAIL_OWNED_RELAY_HOSTS", "mail.oap.example")
    monkeypatch.setenv("OAP_MAIL_SMTP_HOST", "mail.oap.example")
    monkeypatch.setenv("OAP_MAIL_SMTP_PORT", "465")
    monkeypatch.setenv("OAP_MAIL_FROM_ADDRESS", "transport@oap.example")
    monkeypatch.setenv("OAP_MAIL_SMTP_USERNAME", "oap-transport")
    monkeypatch.setenv("OAP_MAIL_SMTP_PASSWORD", "secret-for-test")


def test_oap_mail_fails_closed_when_unconfigured(monkeypatch):
    _clear(monkeypatch)
    state = mail_outbound.status()
    assert state["send_enabled"] is False
    assert state["relay_configured"] is False
    assert state["recipient_delivery_proven"] is False
    with pytest.raises(mail_outbound.MailUnavailable, match="oap_mail_send_disabled"):
        mail_outbound.send(
            recipients=["partnerships@example.com"],
            subject="OAP Transport",
            body="hello",
        )


def test_oap_mail_rejects_non_owned_relay(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OAP_MAIL_SEND_ENABLED", "true")
    monkeypatch.setenv("OAP_MAIL_OWNED_RELAY_HOSTS", "mail.oap.example")
    monkeypatch.setenv("OAP_MAIL_SMTP_HOST", "smtp.external.example")
    monkeypatch.setenv("OAP_MAIL_SMTP_PORT", "465")
    monkeypatch.setenv("OAP_MAIL_FROM_ADDRESS", "transport@oap.example")
    monkeypatch.setenv("OAP_MAIL_SMTP_USERNAME", "user")
    monkeypatch.setenv("OAP_MAIL_SMTP_PASSWORD", "pass")

    assert mail_outbound.status()["relay_host_allowlisted"] is False
    with pytest.raises(mail_outbound.MailUnavailable, match="oap_mail_relay_not_configured"):
        mail_outbound.send(
            recipients="partnerships@example.com",
            subject="OAP Transport",
            body="hello",
        )


def test_oap_mail_uses_tls_and_reports_relay_acceptance_only(monkeypatch):
    _clear(monkeypatch)
    _configured(monkeypatch)
    observed = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout, context):
            observed["host"] = host
            observed["port"] = port
            observed["timeout"] = timeout
            observed["context"] = context

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def login(self, username, password):
            observed["username"] = username
            observed["password"] = password

        def send_message(self, message):
            observed["message"] = message
            return {}

    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    receipt = mail_outbound.send(
        recipients=["partnerships@example.com"],
        subject="OAP Transport × Shared E-Bikes",
        body="Requesting read-only GBFS access.",
    )

    assert observed["host"] == "mail.oap.example"
    assert observed["port"] == 465
    assert observed["context"] is not None
    assert observed["message"]["From"] == "transport@oap.example"
    assert receipt["accepted_by_relay"] is True
    assert receipt["recipient_delivery_proven"] is False
    assert receipt["final_delivery_status"] == "unknown_after_relay_acceptance"


def test_oap_mail_relay_rejection_is_not_green(monkeypatch):
    _clear(monkeypatch)
    _configured(monkeypatch)

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def login(self, username, password):
            return None

        def send_message(self, message):
            return {"blocked@example.com": (550, b"rejected")}

    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    with pytest.raises(
        mail_outbound.MailUnavailable,
        match="oap_mail_relay_rejected_recipient",
    ):
        mail_outbound.send(
            recipients=["blocked@example.com"],
            subject="OAP Transport",
            body="hello",
        )


def test_oap_mail_validates_message_bounds(monkeypatch):
    _clear(monkeypatch)
    _configured(monkeypatch)

    with pytest.raises(ValueError, match="invalid_recipient"):
        mail_outbound.send(recipients=["not-an-email"], subject="x", body="y")
