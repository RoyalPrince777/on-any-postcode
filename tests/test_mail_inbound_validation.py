"""Unit tests for the isolated OAP Mail inbound validation foundation."""
import unittest

from mission_control.mail_inbound_validation import (
    InboundMessageRejected,
    parse_inbound_message,
)


class InboundValidationTests(unittest.TestCase):
    def test_plain_text(self):
        item = parse_inbound_message(
            b"From: Alice <alice@example.org>\r\n"
            b"To: founder@example.org\r\n"
            b"Subject: Hello\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n\r\nHi Founder"
        )
        self.assertEqual(item.correspondent, "alice@example.org")
        self.assertEqual(item.subject, "Hello")
        self.assertEqual(item.body, "Hi Founder")

    def test_reject_empty_or_oversized(self):
        for payload in (b"", b"x" * 256001):
            with self.subTest(size=len(payload)):
                with self.assertRaises(InboundMessageRejected):
                    parse_inbound_message(payload)

    def test_reject_duplicate_sender(self):
        with self.assertRaises(InboundMessageRejected):
            parse_inbound_message(
                b"From: a@example.org\r\nFrom: b@example.org\r\n"
                b"Subject: Hello\r\n\r\nBody"
            )

    def test_reject_html(self):
        with self.assertRaises(InboundMessageRejected):
            parse_inbound_message(
                b"From: a@example.org\r\nSubject: Hello\r\n"
                b"Content-Type: text/html\r\n\r\n<script>bad()</script>"
            )

    def test_reject_attachment(self):
        with self.assertRaises(InboundMessageRejected):
            parse_inbound_message(
                b"From: a@example.org\r\nSubject: Hello\r\n"
                b"Content-Disposition: attachment\r\n\r\nfile"
            )


if __name__ == "__main__":
    unittest.main()
