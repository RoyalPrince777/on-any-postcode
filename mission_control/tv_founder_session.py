"""Server-side Founder session proof for private OAP TV playback.

Accept only the Cookie header read by trusted HTTP server code. This helper
does not prove media ownership, rights, entitlement or storage integrity.
"""
from __future__ import annotations

import hmac

from . import founder_local_auth


def verified_founder_identity(cookie_header: object) -> str | None:
    """Return canonical Founder identity only for a valid signed session."""
    if not isinstance(cookie_header, str) or not cookie_header:
        return None
    try:
        user = founder_local_auth.session_user(cookie_header)
        if not isinstance(user, dict):
            return None
        identity = user.get("id")
        canonical = founder_local_auth.resolved_identity()
        if (
            isinstance(identity, str)
            and isinstance(canonical, str)
            and hmac.compare_digest(identity, canonical)
        ):
            return canonical
    except (ValueError, TypeError, founder_local_auth.FounderLocalAuthUnavailable):
        return None
    return None
