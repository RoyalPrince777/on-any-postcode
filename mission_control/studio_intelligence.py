"""Canonical Founder-facing OAP Studio Intelligence contract.

Studio is the private creation and media-intelligence workspace powered by SMI.
SMI Chat may capture media and route it here; it must not duplicate Studio's media
reasoning, creation, editing or packaging engine. Studio does not expand execution,
publishing, rights, payment or distribution authority. Human Authority remains
final and external delivery stays locked until its existing proof gates pass.
The public Spot does not expose this Founder-only surface.
"""

from __future__ import annotations

from typing import Any

STUDIO_ID = "oap-studio-intelligence"
STUDIO_NAME = "OAP Studio Intelligence"
TABS = (
    "Home",
    "Projects",
    "Bring In",
    "Create",
    "Shape",
    "Intelligence",
    "Rights",
    "Release",
    "Campaign",
    "Analyse",
    "Chronicle",
)
PIPELINE = (
    "Create",
    "Shape",
    "Package",
    "Rights",
    "Release",
    "Distribute",
    "Campaign",
    "Analyse",
    "Chronicle",
)
PRIMARY_ACTIONS = (
    "New Project",
    "Bring In",
    "Capture",
    "Imagine",
    "Shape",
    "Studio Intelligence",
    "Rights",
    "Prepare Release",
    "Chronicle",
)
CREATION_MODES = (
    "Imagine",
    "Bring Alive",
    "Rework",
    "Extend",
    "Clean",
    "Reframe",
    "Restyle",
    "Build Variations",
    "Lock Look",
    "Match Scene",
)
INTELLIGENCE_ROLES = (
    "Director",
    "Producer",
    "Story Intelligence",
    "Scene Intelligence",
    "Sound Intelligence",
    "Visual Intelligence",
    "Audience Intelligence",
    "Release Intelligence",
    "Rights Intelligence",
    "Chronicle Intelligence",
)
STUDIO_COUNCIL = (
    "Director",
    "Producer",
    "Visual",
    "Sound",
    "Story",
    "Rights",
    "Release",
)
REVIEW_DEPTHS = (3, 7, 21)

MEDIA = (
    "image",
    "audio",
    "video",
    "documents",
    "music",
    "campaigns",
    "creator products",
)
CAPTURE_INPUTS = (
    "device",
    "camera",
    "voice",
    "screen",
    "image attachment",
    "audio attachment",
    "video attachment",
    "document attachment",
    "spreadsheet attachment",
    "presentation attachment",
    "url",
    "project folder",
    "OAP World",
    "The Spot",
    "Chronicle",
    "OAP Music",
    "OAP TV & Media",
    "My Shop",
    "The Link",
)
ENTRY_POINTS = (
    "SMI Chat",
    "OAP Studio Intelligence",
)
DESTINATIONS = (
    "Pulse",
    "Signal",
    "OAP TV & Media",
    "OAP Music",
    "OAP Radio",
    "OAP Player",
    "OAP Records",
    "OAP Distribution",
    "Market",
    "My Shop",
    "Chronicle",
    "The Spot",
)
OUTPUT_PACKS = (
    "Pulse Cut",
    "Signal Pack",
    "TV Master",
    "Radio Cut",
    "Music Pack",
    "Player Version",
    "Market Pack",
    "My Shop Pack",
    "Activity Pack",
    "Chronicle Master",
)
SPOT_PLACEMENT = {
    "public_surface": "OAP Studio",
    "private_engine": "OAP Studio Intelligence",
    "position": "after Activity / Adventure and before Explorer / Market",
    "public_private_boundary": "The public Spot never exposes Founder-only SMI controls.",
}

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
        "tabs": list(TABS),
        "pipeline": list(PIPELINE),
        "primary_actions": list(PRIMARY_ACTIONS),
        "creation_modes": list(CREATION_MODES),
        "intelligence_roles": list(INTELLIGENCE_ROLES),
        "studio_council": list(STUDIO_COUNCIL),
        "review_depths": list(REVIEW_DEPTHS),
        "media": list(MEDIA),
        "capture_inputs": list(CAPTURE_INPUTS),
        "entry_points": list(ENTRY_POINTS),
        "destinations": list(DESTINATIONS),
        "output_packs": list(OUTPUT_PACKS),
        "spot_placement": dict(SPOT_PLACEMENT),
        "activation_prompt": ACTIVATION_PROMPT,
        "mode": "Founder creation workspace; recommendation and preparation only",
        "purpose": (
            "Canonical OAP media intelligence for creating, analysing and preparing OAP-owned "
            "media, releases, campaigns and creator products before governed publishing or distribution."
        ),
        "alignment": {
            "smi_chat_is_entry_surface": True,
            "studio_is_canonical_media_engine": True,
            "duplicate_studio_engine_allowed": False,
            "capture_does_not_grant_execution": True,
            "one_source_many_outputs": True,
            "studio_creates_destinations_publish": True,
            "public_studio_private_intelligence_separated": True,
        },
        "governance": {
            "human_authority_final": True,
            "rights_proof_required": True,
            "external_distribution_locked_until_proof": True,
            "payment_authority_granted": False,
            "publishing_authority_granted": False,
            "execution_authority_granted": False,
        },
    }
