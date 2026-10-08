"""Founder-only SMTP envelope routing contract tests."""
import uuid

import pytest

from mission_control.mail_inbound_envelope import validate_founder_delivery
from mission_control.mail_inbound_validation import InboundMessageRejected

RAW = b"From: sender@example.net\r\nTo: wrong@example.org\r\nSubject: Hello\r\n\r\nHello"


def test_founder_envelope_overrides_untrusted_to_header():
    owner = str(uuid.uuid4())
    delivery = validate_founder_delivery(
        envelope_recipient="Founder@Example.org",
        founder_address="founder@example.org",
        founder_owner_id=owner,
        raw_message=RAW,
    )
    assert delivery.owner_id == owner
    assert delivery.recipient == "founder@example.org"
    assert delivery.message.subject == "Hello"


@pytest.mark.parametrize("recipient", [
    "public@example.org", "founder@example.org\r\nBcc: attacker@example.org",
    "Founder <founder@example.org>", "", "founder@example.org,other@example.org",
])
def test_reject_nonfounder_or_malformed_envelope(recipient):
    with pytest.raises(InboundMessageRejected):
        validate_founder_delivery(
            envelope_recipient=recipient,
            founder_address="founder@example.org",
            founder_owner_id=str(uuid.uuid4()),
            raw_message=RAW,
        )


def test_reject_invalid_owner():
    with pytest.raises(InboundMessageRejected, match="invalid_inbound_owner"):
        validate_founder_delivery(
            envelope_recipient="founder@example.org",
            founder_address="founder@example.org",
            founder_owner_id="not-a-uuid",
            raw_message=RAW,
        )
