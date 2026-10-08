"""Founder-only SMTP protocol adapter tests (no live network service)."""
import uuid

from mission_control import mail_inbound_smtp
from mission_control.mail_inbound_store import (
    InboundStoreReceipt,
    InboundStoreUnavailable,
)


def session(*, authenticated=True):
    return mail_inbound_smtp.FounderSmtpSession(
        founder_address="founder@example.org",
        founder_owner_id=str(uuid.uuid4()),
        authenticated_transport=authenticated,
    )


def prepare(s):
    assert s.mail_from("sender@example.net")[0] == 250
    assert s.rcpt_to("founder@example.org")[0] == 250
    assert s.start_data()[0] == 354


def test_authentication_required():
    s = session(authenticated=False)
    assert s.mail_from("sender@example.net")[0] == 530
    assert s.rcpt_to("founder@example.org")[0] == 503


def test_founder_recipient_only():
    s = session()
    assert s.mail_from("sender@example.net")[0] == 250
    assert s.rcpt_to("other@example.org")[0] == 550
    assert s.rcpt_to("founder@example.org")[0] == 250
    assert s.rcpt_to("founder@example.org")[0] == 452


def test_commit_before_success_ack(monkeypatch):
    s = session()
    prepare(s)
    calls = []

    def store(delivery, *, delivery_key):
        calls.append((delivery, delivery_key))
        return InboundStoreReceipt(item_id=str(uuid.uuid4()), inserted=True)

    monkeypatch.setattr(mail_inbound_smtp, "persist_founder_inbox", store)
    for line in (
        b"From: sender@example.net",
        b"Subject: Hello",
        b"",
        b"Message body",
    ):
        assert s.data_line(line, delivery_key="event-1") is None
    assert not calls
    assert s.data_line(b".", delivery_key="event-1")[0] == 250
    assert len(calls) == 1
    assert calls[0][1] == "event-1"
    assert calls[0][0].message.body == "Message body"
    assert s.recipient is None


def test_storage_failure_returns_transient_error(monkeypatch):
    s = session()
    prepare(s)

    def fail(*args, **kwargs):
        raise InboundStoreUnavailable("offline")

    monkeypatch.setattr(mail_inbound_smtp, "persist_founder_inbox", fail)
    for line in (b"From: sender@example.net", b"Subject: Hello", b"", b"Body"):
        s.data_line(line, delivery_key="event-2")
    assert s.data_line(b".", delivery_key="event-2")[0] == 451
    assert s.sender is None


def test_size_limit_rejects_before_persist(monkeypatch):
    s = session()
    prepare(s)
    monkeypatch.setattr(mail_inbound_smtp, "persist_founder_inbox", lambda *a, **kw: None)
    assert s.data_line(b"x" * (mail_inbound_smtp.MAX_MESSAGE_BYTES + 1), delivery_key="event-3")[0] == 552


def test_dot_transparency(monkeypatch):
    s = session()
    prepare(s)
    captured = []

    def store(delivery, *, delivery_key):
        captured.append(delivery.message.body)

    monkeypatch.setattr(mail_inbound_smtp, "persist_founder_inbox", store)
    for line in (b"From: sender@example.net", b"Subject: Hello", b"", b"..leading"):
        s.data_line(line, delivery_key="event-4")
    assert s.data_line(b".", delivery_key="event-4")[0] == 250
    assert captured == [".leading"]
