"""Bounded Founder-only SMTP protocol adapter; no network listener is started.

Use only behind a separately authenticated, TLS-enforced transport. This
adapter does not establish authentication, TLS, DNS MX or production delivery.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .mail_inbound_envelope import InboundMessageRejected, _mailbox_address, validate_founder_delivery
from .mail_inbound_store import InboundStoreUnavailable, persist_founder_inbox

MAX_MESSAGE_BYTES = 256000


@dataclass
class FounderSmtpSession:
    founder_address: str
    founder_owner_id: str
    authenticated_transport: bool = False
    sender: str | None = None
    recipient: str | None = None
    data_lines: list[bytes] = field(default_factory=list)
    data_size: int = 0
    receiving: bool = False

    def reset(self) -> None:
        self.sender = None
        self.recipient = None
        self.data_lines.clear()
        self.data_size = 0
        self.receiving = False

    def mail_from(self, sender: str) -> tuple[int, str]:
        self.reset()
        if not self.authenticated_transport:
            return 530, "Authenticated transport required"
        try:
            self.sender = _mailbox_address(sender)
        except InboundMessageRejected:
            return 553, "Invalid sender"
        return 250, "Sender accepted"

    def rcpt_to(self, recipient: str) -> tuple[int, str]:
        if not self.sender:
            return 503, "MAIL FROM required"
        try:
            if _mailbox_address(recipient) != _mailbox_address(self.founder_address):
                return 550, "Recipient unavailable"
        except InboundMessageRejected:
            return 550, "Recipient unavailable"
        if self.recipient is not None:
            return 452, "Single recipient only"
        self.recipient = recipient
        return 250, "Recipient accepted"

    def start_data(self) -> tuple[int, str]:
        if not self.sender or not self.recipient:
            return 503, "MAIL FROM and RCPT TO required"
        self.receiving = True
        self.data_lines.clear()
        self.data_size = 0
        return 354, "End with dot on a line by itself"

    def data_line(self, line: bytes, *, delivery_key: str) -> tuple[int, str] | None:
        if not self.receiving:
            return 503, "DATA required"
        if not isinstance(line, bytes) or b"\r" in line or b"\n" in line:
            self.reset()
            return 501, "Invalid DATA line"
        if line == b".":
            raw = b"\r\n".join(self.data_lines) + b"\r\n"
            try:
                delivery = validate_founder_delivery(
                    envelope_recipient=self.recipient,
                    founder_address=self.founder_address,
                    founder_owner_id=self.founder_owner_id,
                    raw_message=raw,
                )
                persist_founder_inbox(delivery, delivery_key=delivery_key)
            except (InboundMessageRejected, ValueError, TypeError):
                return self._finish(554, "Message rejected")
            except InboundStoreUnavailable:
                return self._finish(451, "Temporary local storage failure")
            return self._finish(250, "Message committed")
        # RFC 5321 dot transparency: remove one leading dot.
        if line.startswith(b".."):
            line = line[1:]
        self.data_size += len(line) + 2
        if self.data_size > MAX_MESSAGE_BYTES:
            return self._finish(552, "Message too large")
        self.data_lines.append(line)
        return None

    def _finish(self, code: int, detail: str) -> tuple[int, str]:
        self.reset()
        return code, detail
