"""Fail-closed OAP-owned TURN credential provisioning for Link Up.

Credentials follow Coturn's secret-based TURN REST model: a short-lived
``timestamp:userid`` username and a base64 HMAC-SHA1 credential. The shared
secret never leaves the server. Configuration alone does not certify relay
connectivity; ``ready`` stays false until an explicit relay verification flag is
present after real network proof.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from typing import Any
from urllib.parse import urlsplit

from . import link_relationships, linkup_safety

DEFAULT_TTL_SECONDS = 300
MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 900
SECRET_MIN_BYTES = 32


class LinkTurnUnavailable(RuntimeError):
    pass


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _bool_env(name: str) -> bool:
    return os.environ.get(name, "").strip().casefold() == "true"


def _ttl() -> int:
    raw = os.environ.get("OAP_LINK_TURN_TTL_SECONDS", str(DEFAULT_TTL_SECONDS))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_TTL_SECONDS
    return min(MAX_TTL_SECONDS, max(MIN_TTL_SECONDS, value))


def _valid_turn_url(value: str) -> bool:
    if not value or len(value) > 500 or any(char.isspace() for char in value):
        return False
    parsed = urlsplit(value)
    if parsed.scheme.casefold() not in {"turn", "turns"}:
        return False
    target = parsed.path
    if not target or "@" in target or parsed.fragment:
        return False
    return True


def _turn_urls() -> tuple[str, ...]:
    raw = os.environ.get("OAP_LINK_TURN_URLS", "")
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    if not values or not all(_valid_turn_url(item) for item in values):
        return ()
    return values[:4]


def _secret() -> str:
    return os.environ.get("OAP_LINK_TURN_SHARED_SECRET", "")


def status() -> dict[str, Any]:
    urls = _turn_urls()
    secret = _secret()
    realm = os.environ.get("OAP_LINK_TURN_REALM", "").strip()
    owned = _bool_env("OAP_LINK_TURN_OWNED")
    configured = bool(urls and realm and len(secret.encode("utf-8")) >= SECRET_MIN_BYTES)
    credential_ready = configured and owned
    relay_verified = credential_ready and _bool_env("OAP_LINK_TURN_RELAY_VERIFIED")
    return {
        "configured": configured,
        "owned": owned,
        "credential_ready": credential_ready,
        "relay_verified": relay_verified,
        "ready": relay_verified,
        "url_count": len(urls),
        "ttl_seconds": _ttl(),
    }


def issue_credentials(identity_id: object, recipient_id: object) -> dict[str, Any]:
    identity = _uuid(identity_id, "invalid_identity")
    recipient = _uuid(recipient_id, "invalid_recipient")
    if identity == recipient:
        raise ValueError("cannot_call_self")
    try:
        if linkup_safety.blocked_between(identity, recipient):
            raise ValueError("link_blocked")
        if not link_relationships.accepted_between(identity, recipient):
            raise ValueError("accepted_link_required")
    except ValueError:
        raise
    except (
        linkup_safety.LinkUpSafetyUnavailable,
        link_relationships.LinkRelationshipsUnavailable,
    ) as exc:
        raise LinkTurnUnavailable("turn_relationship_guard_unavailable") from exc

    state = status()
    if not state["credential_ready"]:
        raise LinkTurnUnavailable("turn_credentials_unavailable")

    ttl = int(state["ttl_seconds"])
    expires_at = int(time.time()) + ttl
    username = f"{expires_at}:{identity}"
    digest = hmac.new(
        _secret().encode("utf-8"),
        username.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    credential = base64.b64encode(digest).decode("ascii")
    urls = list(_turn_urls())
    if not urls:
        raise LinkTurnUnavailable("turn_credentials_unavailable")
    return {
        "ice_servers": [
            {
                "urls": urls,
                "username": username,
                "credential": credential,
                "credentialType": "password",
            }
        ],
        "expires_at": expires_at,
        "ttl_seconds": ttl,
        "relay_verified": bool(state["relay_verified"]),
    }
