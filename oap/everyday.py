"""OAP EVERYDAY programme catalogue: zero-new-spend, review-only.

Separate direct support from sponsor-funded free rewards. No beneficiary data,
unverified resource links, fabricated partners, or public entries.
"""
from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = (
    ("essentials", "Everyday Essentials", "Food and household essentials"),
    ("energy", "Everyday Energy", "Energy support information"),
    ("move", "Everyday Move", "Transport and access"),
    ("families", "Everyday Families", "Family and school essentials"),
    ("support", "Everyday Support", "Reviewed practical resources"),
    ("rewards", "Everyday Rewards", "Sponsor-funded free prize draws"),
    ("partners", "Everyday Partners", "Sponsor enquiries and commitments"),
)

@dataclass(frozen=True)
class Programme:
    name: str = "OAP EVERYDAY"
    status: str = "proposed"
    spending_required: bool = False
    prizes_secured: bool = False
    entries_open: bool = False
    payments_enabled: bool = False

def catalogue() -> dict[str, object]:
    """Public-safe capability description, not proof of a live campaign."""
    return {
        "name": Programme.name,
        "status": Programme.status,
        "categories": tuple({"key": key, "label": label, "purpose": purpose,
                              "status": "planned"} for key, label, purpose in CATEGORIES),
        "direct_support_requires_draw_entry": False,
        "rewards_engine": "existing_oap_raffles",
        "partners_confirmed": 0,
        "prizes_secured": False,
        "entries_open": False,
        "payments_enabled": False,
        "public_launch_authorised": False,
        "external_provider_required": False,
    }


def propose_partner(*, organisation: str, prize_description: str,
                    consent_to_contact: bool = False) -> dict[str, object]:
    """Create an ephemeral, uncommitted proposal; no contact or persistence."""
    name = str(organisation or "").strip()
    prize = str(prize_description or "").strip()
    if not name or not prize or len(name) > 120 or len(prize) > 280:
        raise ValueError("bounded_partner_and_prize_required")
    return {"organisation": name, "prize_description": prize,
            "status": "proposed_unverified",
            "consent_to_contact": consent_to_contact is True,
            "contact_sent": False, "partner_committed": False,
            "prize_secured": False, "public_listing_allowed": False,
            "entries_open": False, "payments_enabled": False}
