"""JWT token generation and validation for Human Authority."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import logging

logger = logging.getLogger(__name__)


class JWTHandler:
    """RS256 JWT handler for Human Authority authentication."""

    def __init__(self, private_key_path: str, public_key_path: str):
        with open(private_key_path, "r") as f:
            self.private_key = f.read()
        with open(public_key_path, "r") as f:
            self.public_key = f.read()

    def create_token(
        self,
        identity_id: str,
        authority_level: int,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT token for Human Authority.

        Args:
            identity_id: The identity identifier
            authority_level: 0 for level-zero Human Authority
            expires_delta: Token expiration time (default 1 hour)

        Returns:
            Signed JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=1)

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload = {
            "sub": identity_id,
            "authority_level": authority_level,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "type": "access",
        }

        token = jwt.encode(payload, self.private_key, algorithm="RS256")

        logger.info(
            "JWT token created",
            extra={
                "identity_id": identity_id,
                "authority_level": authority_level,
                "expires_in_seconds": int(expires_delta.total_seconds()),
            },
        )

        return token

    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.public_key, algorithms=["RS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise ValueError("Invalid token")
