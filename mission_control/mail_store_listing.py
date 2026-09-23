"""Public first-party OAP Mail information, not a service or release gate.

This standalone informational record has no Mail database, SMI, delivery,
payment, package or installation dependency. Never derive readiness from a
user-supplied gate assertion.
"""
from __future__ import annotations

APP_ID = "oap.mail"


def listing() -> dict[str, object]:
    """Truthful public catalogue information; no executable release surface."""
    return {
        "app_id": APP_ID,
        "name": "OAP Mail",
        "publisher": "ON ANY POSTCODE LTD",
        "distribution": "OAP App Store",
        "first_party": True,
        "tagline": "Your Mail. Your World. Your Control.",
        "description": "First-party OAP Mail. Information page only; release pending.",
        "public_release_state": "release_pending",
        "informational_only": True,
        "mailbox_available": False,
        "delivery_enabled": False,
        "mail_delivery_claimed": False,
        "install_enabled": False,
        "package_available": False,
        "publish_executed": False,
        "end_to_end_encryption_claimed": False,
        "security_certification_claimed": False,
        "human_authority_final": True,
    }
