"""Founder-only SMI alliance board, separate from the canonical agent registry.

Fiction-inspired alliance roles are preserved as *design references*, not
production agents, third-party providers, or execution authorities.
No capability rating or career stars are inferred from membership.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from . import agents

# The recovered 14-person Mission: Impossible advisory design is *not* a
# registration or licensing claim. Existing agent passports stay unchanged.
MISSION_IMPOSSIBLE = (
    "Ethan Hunt", "Luther Stickell", "Benji Dunn", "Ilsa Faust",
    "William Brandt", "Grace", "Jane Carter", "Eugene Kittridge",
    "Alan Hunley", "Paris", "Nyah Nordoff-Hall", "Billy Baird",
    "Swanbeck", "Sean Ambrose",
)
TERMINATOR_CAPABILITIES = (
    "T-800 — resilience and protection",
    "T-1000 — adaptation and recovery",
    "T-X — diagnostics",
    "Rev-9 — coordination",
    "Cameron — human interaction",
    "John Connor — planning",
    "Sarah Connor — protection",
    "Kyle Reese — defensive planning",
)
PREDATOR_CAPABILITIES = (
    "Tracking and sensing", "Environmental awareness",
    "Survival analysis", "Defensive threat modelling",
)
TRANSFORMERS = ("Optimus Prime", "Bumblebee")
BATMAN = ("Batman", "Robin")

# Founder-bounded OAP Home V2 assignment: use existing specialist names and
# existing six intelligence alliances. A named role is not a new agent passport,
# worker, permissions grant, live vote, field observation, or career-star award.
_HOME_V2_MITCHAM_SPECIALISTS: tuple[tuple[str, str, str], ...] = (
    ("SMI", "unified_smi_brain",
     "Unify evidence and recommendations; no independent final authority."),
    ("Captain ALL IN", "mission_coordinator",
     "One Done / Next / Recovery board and exact-source receipts."),
    ("Neo", "existing_specialist",
     "Native Android launcher implementation, compilation and route checks."),
    ("Benji Dunn", "mission_impossible_advisory",
     "V2 APK package, signing-certificate and install compatibility review."),
    ("Fox", "existing_specialist",
     "Local rollback, old-launcher retirement order and Home Node protection."),
    ("Foxy", "separate_identity_pending_canonical_link",
     "Human-facing trust cues and clarity during launcher switching; keep Fox "
     "recovery distinct and do not invent a Foxy passport."),
    ("Shere Khan", "existing_specialist",
     "Adversarial proof challenge: false Green, wrong package and unsafe uninstall."),
    ("Bagheera", "existing_specialist",
     "Guardian-aligned privacy, microphone/camera permissions and consent boundaries."),
    ("Black Box", "contained_ai_research_system",
     "Contained Xenox motherboard AI research: isolation, recovery and unsafe "
     "connectivity failure patterns; not a new agent or service."),
    ("Batman", "batman_alliance_advisory",
     "Forensic bug/incident evidence review inspired by detective methods; "
     "no real police or CID authority."),
    ("Predator Intelligence", "predator_alliance_advisory",
     "On-device environment and sensor-permission failure cases only; "
     "no covert observation or tracking."),
    ("M3GAN", "separate_fictional_research_profile",
     "Adaptive interaction and consent failures; Original and 2.0 are one identity."),
    ("AMELIA", "separate_fictional_research_profile",
     "Distinct adversarial decision/boundary research; no device command access."),
    ("Trinity", "existing_specialist",
     "Real Redmi A5 touch targets, accessibility, navigation and screenshots."),
    ("Keymaker", "existing_specialist",
     "HOME intent, default app selection, back navigation and recovery routes."),
    ("Owl", "existing_specialist",
     "Separate source/CI/device receipts from claims, scores and fiction roles."),
    ("Gorilla", "existing_specialist",
     "Last-line safety: halt release or removal on missing recovery evidence."),
)

_HOME_V2_MITCHAM_ALLIANCES: tuple[tuple[str, str], ...] = (
    ("jungle_book", "Shere Khan and Bagheera: adversarial challenge and protection."),
    ("mission_impossible", "Benji Dunn: native installation, signing and field checklists."),
    ("batman", "Batman: incident forensics and traceable Android failure evidence."),
    ("predator", "Device environment and sensor-permission threat-model review."),
)


def home_v2_mitcham_mission() -> dict[str, Any]:
    """Read-only mission lens over existing roles; does NOT expand any registry.

    Mitcham CR4 is the Founder's intended local device acceptance context,
    not a GPS observation or evidence that the real phone was tested.
    """
    by_name = {
        str(agent["name"]).casefold(): str(agent["agent_id"])
        for agent in agents.AGENT_REGISTRY
    }
    specialists = tuple(
        {
            "name": name,
            "classification": classification,
            "task": task,
            # Only reuse a known canonical passport; do not manufacture one.
            "agent_id": by_name.get(name.casefold())
            if classification == "existing_specialist" else None,
            "status": "assigned_advisory_only",
            "verified_execution": False,
            "earned_stars": None,
        }
        for name, classification, task in _HOME_V2_MITCHAM_SPECIALISTS
    )
    return {
        "id": "oap_home_v2_mitcham",
        "title": "OAP Home V2 · Mitcham Android field mission",
        "scope": "founder_private_read_only",
        "location": "Mitcham CR4 — intended local test context, not verified geolocation",
        "phone": "Redmi A5 — physical acceptance not verified",
        "decision": "Keep com.onanypostcode.oaphome.v2; display OAP Home; "
                    "retire com.onanypostcode.oaphome only after safe acceptance.",
        "smi_command": "Sovereign Megaverse Intelligence",
        "founder_final": True,
        "specialists": specialists,
        "alliance_refs": tuple(
            {"id": alliance_id, "mission_fit": why}
            for alliance_id, why in _HOME_V2_MITCHAM_ALLIANCES
        ),
        "research_identities_separate": ("M3GAN", "AMELIA", "Black Box"),
        "m3gan_identity_rule": "M3GAN Original → 2.0: one continuous identity.",
        "black_box_identity_rule": "Contained Xenox motherboard AI research system; "
                                   "not an SMI agent passport, not a new brain.",
        "optional_not_activated": (
            "Terminator Intelligence — recovery resilience overlay only",
            "Transformers Intelligence — handoff resilience reference only",
        ),
        "release_gates": (
            "V2 package and signer from installed device",
            "Exact-head signed candidate with newer versionCode",
            "Native Android default HOME and independent stock Home recovery",
            "User-approved retirement of exact legacy Home package",
            "Founder Final",
        ),
        "activated": False,
        "device_acceptance_verified": False,
        "legacy_home_uninstalled": False,
        "agent_passports_created": 0,
        "official_stars_awarded": 0,
        "recorded_independent_votes": 0,
        "can_approve": False,
        "can_execute": False,
    }


# Dated advisory snapshot recovered from the Founder's earlier SMI discussions.
# Ratings are historical role-fit assessments, NOT career achievement awards.
# Some historical labels have no current passport and must stay unregistered.
HISTORICAL_TOP_21_2026_10_15: tuple[tuple[str, int], ...] = (
    ("Gyata", 7),
    ("Captain ALL IN", 7),
    ("Neo", 7),
    ("Nirmata", 7),
    ("Shere Khan", 7),
    ("Bagheera", 7),
    ("Oracle", 7),
    ("Octopus", 7),
    ("Owl", 7),
    ("Elephant", 7),
    ("Queen Bee", 7),
    ("Fox", 7),
    ("Panther", 6),
    ("Eagle", 6),
    ("Gorilla", 6),
    ("Tigress", 6),
    ("Lioness", 6),
    ("Spider", 6),
    ("Falcon", 6),
    ("Bee Swarm", 6),
    ("Keymaker", 6),
)


def _historical_top_21(career_stars: Mapping[str, int]) -> tuple[dict[str, Any], ...]:
    """Link dated references only to exact canonical agent names.

    Never register unknown historical names, infer aliases, or confer rank-based
    permissions/achievement stars.
    """
    by_name = {str(agent["name"]).casefold(): str(agent["agent_id"])
               for agent in agents.AGENT_REGISTRY}
    return tuple(
        {
            "rank": index,
            "name": name,
            "historical_rating": rating,
            "historical_rating_max": 7,
            "agent_id": by_name.get(name.casefold()),
            "registry_linked": name.casefold() in by_name,
            "career_stars": career_stars.get(by_name[name.casefold()], 0)
            if name.casefold() in by_name else None,
        }
        for index, (name, rating)
        in enumerate(HISTORICAL_TOP_21_2026_10_15, start=1)
    )


def get_founder_alliance_board(
    *, career_rankings: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Expose recovered design alliances without granting agent status.

    The Jungle Book listing is projected from the canonical registry. The
    others are recorded *unranked* until a separately approved canonical
    identity and independently reviewed evidence exist.
    """
    stars_by_id = {
        str(row["agent_id"]): int(row["achievement_stars"])
        for row in career_rankings
    }
    jungle_book = tuple(
        {"name": str(agent["name"]), "agent_id": str(agent["agent_id"]),
         "ranking_eligible": True}
        for agent in agents.AGENT_REGISTRY
        if agent["family_id"] == "jungle_book"
    )
    def unregistered(names: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
        return tuple(
            {"name": name, "agent_id": None, "ranking_eligible": False}
            for name in names
        )

    return {
        "scope": "founder_only_read_only",
        "status": "advisory_roster_reference",
        "human_authority": "Founder Final",
        "smi": {
            "name": "SMI",
            "kind": "intelligence_brain",
            "command_position": "Above specialist agent rankings",
            "career_ranking_eligible": False,
        },
        "mission_coordinator": {
            "name": "Captain ALL IN",
            "kind": "mission_coordination_role",
            "ranking": "Separate from canonical agent achievement totals",
        },
        "historical_top_21": {
            "as_of": "2026-10-15",
            "source": "Recovered Founder conversation snapshot; not runtime evidence",
            "rating_kind": "historical_advisory_role_fit",
            "separate_from_career_stars": True,
            "entries": _historical_top_21(stars_by_id),
        },
        "oversight": ("Guardian", "HRM Core"),
        "home_v2_mitcham_mission": home_v2_mitcham_mission(),
        "alliances": (
            {
                "id": "jungle_book", "name": "Jungle Book Intelligence",
                "status": "canonical_registered_family",
                "members": jungle_book,
            },
            {
                "id": "mission_impossible", "name": "Mission: Impossible Intelligence",
                "status": "recovered_advisory_design_only",
                "members": unregistered(MISSION_IMPOSSIBLE),
            },
            {
                "id": "terminator", "name": "Terminator Intelligence",
                "status": "existing_agent_capability_overlay_only",
                "members": unregistered(TERMINATOR_CAPABILITIES),
                "threat_models_not_agents": ("Skynet", "Legion"),
            },
            {
                "id": "predator", "name": "Predator Intelligence",
                "status": "existing_agent_capability_overlay_only",
                "members": unregistered(PREDATOR_CAPABILITIES),
            },
            {
                "id": "transformers", "name": "Transformers Intelligence",
                "status": "recovered_design_only",
                "members": unregistered(TRANSFORMERS),
            },
            {
                "id": "batman", "name": "Batman Intelligence",
                "status": "recovered_design_only",
                "members": unregistered(BATMAN),
            },
        ),
        "rank_policy": (
            "Existing approved agent rankings are unchanged. No invented "
            "rank numbers, no automatic stars, no duplicated passports; "
            "SMI is the coordinating brain, not a competing agent."
        ),
        "live_activation_claimed": False,
        "can_approve": False,
        "can_execute": False,
    }
