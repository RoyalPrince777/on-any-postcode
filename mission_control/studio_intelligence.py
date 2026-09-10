"""Canonical Founder-facing OAP Studio Intelligence contract.

Studio is the creation workspace powered by SMI. It does not expand execution,
publishing, rights, payment or distribution authority. Human Authority remains
final and external delivery stays locked until its existing proof gates pass.
"""

from __future__ import annotations

from typing import Any

STUDIO_ID = "oap-studio-intelligence"
STUDIO_NAME = "OAP Studio Intelligence"
PIPELINE = (
    "Create",
    "Edit",
    "Package",
    "Rights",
    "Publish",
    "Distribute",
    "Campaign",
    "Analyse",
)
MEDIA = (
    "image",
    "audio",
    "video",
    "documents",
    "music",
    "campaigns",
    "creator products",
)
DESTINATIONS = (
    "OAP Music",
    "OAP Player",
    "OAP Radio",
    "OAP TV & Media",
    "OAP Records",
    "OAP Distribution",
    "My Shop",
    "The Spot",
)
ACTIVATION_PROMPT = (
    "OAP Studio Intelligence mode. Help me create, edit, package, check rights, "
    "prepare publishing, distribution, campaign and analysis for: "
)


def status() -> dict[str, Any]:
    """Return the secret-free Studio contract for the Founder workbench."""

    return {
        "id": STUDIO_ID,
        "name": STUDIO_NAME,
        "ready": True,
        "powered_by": "SMI",
        "pipeline": list(PIPELINE),
        "media": list(MEDIA),
        "destinations": list(DESTINATIONS),
        "activation_prompt": ACTIVATION_PROMPT,
        "mode": "Founder creation workspace; recommendation and preparation only",
        "purpose": (
            "Create and prepare OAP-owned media, releases, campaigns and creator products "
            "before governed publishing or distribution."
        ),
        "governance": {
            "human_authority_final": True,
            "rights_proof_required": True,
            "external_distribution_locked_until_proof": True,
            "payment_authority_granted": False,
            "publishing_authority_granted": False,
            "execution_authority_granted": False,
        },
    }
