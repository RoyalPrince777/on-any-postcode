"""Multi-Factor Authentication (MFA) using TOTP."""

from __future__ import annotations

import base64
import binascii
import io
import logging

import pyotp
import qrcode

logger = logging.getLogger(__name__)


class MFAHandler:
    """Time-based One-Time Password (TOTP) MFA handler."""

    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret for MFA setup.

        Returns:
            Base32-encoded TOTP secret
        """
        secret = pyotp.random_base32()
        logger.debug("TOTP secret generated")
        return secret

    @staticmethod
    def get_provisioning_uri(secret: str, name: str, issuer: str = "ON ANY POSTCODE") -> str:
        """Generate provisioning URI for QR code.

        Args:
            secret: TOTP secret
            name: Identity name (email or ID)
            issuer: Issuer name for QR code

        Returns:
            Provisioning URI (otpauth://)
        """
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=name, issuer_name=issuer)
        return uri

    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """Generate QR code as base64-encoded PNG.

        Args:
            uri: Provisioning URI from get_provisioning_uri()

        Returns:
            Base64-encoded PNG image
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        return base64.b64encode(buffer.getvalue()).decode()

    @staticmethod
    def verify_totp(secret: str, code: str) -> bool:
        """Verify TOTP code.

        Args:
            secret: TOTP secret
            code: 6-digit code from authenticator app

        Returns:
            True if code is valid (allows 30-second window for clock drift)
        """
        try:
            totp = pyotp.TOTP(secret)
            # valid_window=1 allows 30s before and after current window
            is_valid = totp.verify(code, valid_window=1)
            if not is_valid:
                logger.warning("TOTP verification failed")
            return is_valid
        except (binascii.Error, OverflowError, TypeError, ValueError) as exc:
            logger.error("TOTP verification error: %s", exc)
            return False

    @staticmethod
    def generate_recovery_codes(count: int = 10) -> list[str]:
        """Generate backup recovery codes (in case device is lost).

        Args:
            count: Number of recovery codes to generate

        Returns:
            List of recovery codes (alphanumeric, 8 characters each)
        """
        import secrets

        codes = [secrets.token_urlsafe(6) for _ in range(count)]
        logger.info(f"Generated {count} recovery codes")
        return codes
