"""Advisory protocol-specific SMI team selection; no authority or agent execution."""
from __future__ import annotations

from dataclasses import dataclass

# Named specialist roles are recommendations, not verified active agent processes.
PROTOCOL_TEAMS: dict[str, tuple[str, tuple[str, ...]]] = {
    "coordination": ("Captain ALL IN", ("Oracle", "Octopus", "Gyata")),
    "creation": ("NIRMATA", ("Architect", "Tigress", "Benji")),
    "execution": ("Neo", ("Trinity", "Tigress")),
    "stealth": ("Bagheera", ("Batman", "Luther", "Ilsa")),
    "guardian": ("Guardian", ("Seraph", "Gorilla", "Bagheera")),
    "adversarial": ("Shere Khan", ("Agent Smith", "Shark")),
    "pack": ("Akela", ("Octopus",)),
    "swarm": ("Queen Bee", ("Spider",)),
    "patterns": ("Octopus", ("Oracle", "Lucy", "Owl")),
    "dependencies": ("Spider", ("Architect", "Keymaker")),
    "recovery": ("Fox", ("Dozer", "Tank", "Benji")),
    "last_line_defence": ("Gorilla", ("Guardian", "Gyata")),
    "command": ("Gyata", ("Lioness", "Tigress")),
    "memory": ("Hathi", ("Elephant",)),
    "investigation": ("Batman", ("Robin", "Oracle", "Shere Khan")),
    "complex_missions": ("Ethan Hunt", ("Luther", "Benji", "Ilsa")),
    "matrix": ("Morpheus", ("Neo", "Trinity", "Oracle")),
    "identity": ("Seraph", ("Keymaker", "Guardian")),
    "verification": ("Tigress", ("The Twins", "Oracle")),
    "audit": ("HRM", ("Hathi", "Oracle")),
    "economics": ("MANSA", ("Owl", "Octopus", "Tigress")),
    "civic_rights": ("Batman", ("Nyah", "Ilsa", "Bagheera")),
    "language": ("NYANSA", ("Lucy", "Morpheus")),
    "science": ("NIRMATA", ("Lucy", "Octopus", "Tigress")),
    "threat_awareness": ("Shark", ("Eagle", "Owl", "Guardian")),
    "living_kernel": ("Architect", ("Neo", "Tank", "Guardian")),
    "deployment": ("Neo", ("Benji", "Trinity", "Dozer")),
    "green_gate": ("Independent verification", ("Tigress", "Oracle", "Guardian")),
}


@dataclass(frozen=True)
class ProtocolRecommendation:
    protocol: str
    lead: str | None
    specialists: tuple[str, ...]
    status: str
    advisory_only: bool = True
    grants_permissions: bool = False
    human_authority_final: bool = True


def recommend_protocol_team(protocol: str) -> ProtocolRecommendation:
    """Return advisory candidates; unknown input fails closed without fallback authority."""
    if not isinstance(protocol, str):
        return ProtocolRecommendation("", None, (), "UNRECOGNISED")
    key = protocol.strip().lower()
    team = PROTOCOL_TEAMS.get(key)
    if team is None:
        return ProtocolRecommendation(key, None, (), "UNRECOGNISED")
    return ProtocolRecommendation(key, team[0], team[1], "PROPOSED_UNVERIFIED")
