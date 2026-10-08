"""Adversarial protocol-boundary tests; these do not claim network security."""
import uuid

from mission_control import mail_inbound_smtp
from mission_control.mail_inbound_store import InboundStoreUnavailable


def make_session():
    return mail_inbound_smtp.FounderSmtpSession(
        founder_address="founder@example.org",
        founder_owner_id=str(uuid.uuid4()),
        authenticated_transport=True,
    )


def test_data_cannot_start_before_envelope():
    s = make_session()
    assert s.start_data()[0] == 503
    assert s.data_line(b"From: attacker@example.org", delivery_key="key")[0] == 503


def test_invalid_sender_does_not_authorize_recipient():
    s = make_session()
    assert s.mail_from("attacker\r\nRCPT TO:<founder@example.org>")[0] == 553
    assert s.rcpt_to("founder@example.org")[0] == 503


def test_rejected_recipient_cannot_enter_data():
    s = make_session()
    assert s.mail_from("sender@example.net")[0] == 250
    assert s.rcpt_to("outsider@example.org")[0] == 550
    assert s.start_data()[0] == 503


def test_failed_persistence_never_returns_success(monkeypatch):
    s = make_session()
    assert s.mail_from("sender@example.net")[0] == 250
    assert s.rcpt_to("founder@example.org")[0] == 250
    assert s.start_data()[0] == 354

    def unavailable(*args, **kwargs):
        raise InboundStoreUnavailable("database unavailable")

    monkeypatch.setattr(mail_inbound_smtp, "persist_founder_inbox", unavailable)
    for line in (b"From: sender@example.net", b"Subject: Test", b"", b"Body"):
        assert s.data_line(line, delivery_key="stable-transport-event") is None
    assert s.data_line(b".", delivery_key="stable-transport-event")[0] == 451
    assert not s.receiving
    assert s.recipient is None


def test_oversized_data_resets_session():
    s = make_session()
    assert s.mail_from("sender@example.net")[0] == 250
    assert s.rcpt_to("founder@example.org")[0] == 250
    assert s.start_data()[0] == 354
    assert s.data_line(b"x" * (mail_inbound_smtp.MAX_MESSAGE_BYTES + 1), delivery_key="key")[0] == 552
    assert s.data_line(b".", delivery_key="key")[0] == 503
    assert s.recipient is None


def test_new_mail_from_discards_previous_uncommitted_data():
    s = make_session()
    assert s.mail_from("sender@example.net")[0] == 250
    assert s.rcpt_to("founder@example.org")[0] == 250
    assert s.start_data()[0] == 354
    assert s.data_line(b"From: sender@example.net", delivery_key="key") is None
    assert s.mail_from("second@example.net")[0] == 250
    assert s.data_lines == []
    assert s.recipient is None
    assert not s.receiving
