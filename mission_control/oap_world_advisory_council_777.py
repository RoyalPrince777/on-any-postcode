"""OAP World council: advisory-only immutable proposal projection.

This module does not activate agents, execute work, authorize dispatch or count
fictional dialogue as live votes. Existing canonical registries remain authoritative.
"""
from __future__ import annotations

from typing import Any

ROLES = (
    ("Lion / Gyata", "One coherent World identity and Founder authority"),
    ("Octopus", "Reuse shared infrastructure, no duplicate dispatch engine"),
    ("Fox", "Recover interrupted journeys without duplicate execution"),
    ("Eagle", "Local-first discovery and global expansion"),
    ("Leopard", "Simplify the reliable customer journey"),
    ("Owl", "Explain evidence and reasons for recommendations"),
    ("Wolf / Akela", "Accountable community trust and support"),
    ("Dolphin", "Accessible and welcoming communication"),
    ("Ant", "Decompose requests into verifiable tasks"),
    ("Cheetah", "Low-memory phone-first performance"),
    ("Buffalo", "Resilience before cosmetic features"),
    ("Falcon", "Surface the most relevant next action"),
    ("Bear", "Operational continuity"),
    ("Elephant / Hathi", "Preserve original histories and corrections"),
    ("Rhino", "Permissions and misuse boundaries"),
    ("Tiger / Shere Khan", "Adversarial false-readiness checks"),
    ("Crocodile", "Defensive fraud and threat detection"),
    ("Monkey", "Creative discovery and assumption challenges"),
    ("Spider", "Dependencies and duplication prevention"),
    ("Bee / Queen Bee", "Bounded coordination without new authority"),
    ("Whale", "Long-term cultural and institutional memory"),
)

PACK = ("Akela", "Raksha", "Father Wolf", "Grey Brother", "Phao")
ROUNDS = (
    ("World identity", "Gyata + Eagle", "KEEP"),
    ("Four movement services", "Octopus + Spider", "KEEP"),
    ("Community trust", "Akela + Bagheera", "UPGRADE"),
    ("Truth and safety", "Shere Khan + Guardian", "UPGRADE"),
    ("Continuity", "Fox + Gorilla", "UPGRADE"),
    ("History and culture", "Hathi + Baloo", "KEEP"),
    ("Speed and simplicity", "Cheetah + Falcon", "UPGRADE"),
)
BLOCKED = (
    "real_world_dispatch", "payment_capture", "unproven_reservation_confirmation",
    "hidden_tracking", "private_media_leak", "autonomous_approval",
)

def advisory_council() -> dict[str, Any]:
    """Return fresh read-only proposal data, with no external side effects."""
    return {
        "status": "advisory_only",
        "founder_final_required": True,
        "live_agent_votes_verified": False,
        "agent_runtime_activated": False,
        "implementation_vpi": None,
        "roles": [{"name": name, "recommendation": proposal} for name, proposal in ROLES],
        "permanent_wolf_pack": list(PACK),
        "rounds": [
            {"number": i, "subject": subject, "lead": lead, "decision": decision}
            for i, (subject, lead, decision) in enumerate(ROUNDS, 1)
        ],
        "blocked_capabilities": list(BLOCKED),
    }
