"""Proposed MI specialists: advisory-only, not wired into the locked canonical registry.

The founder-approved roles below are design metadata, not running agents.
No provider, tool, execution, or authority is assigned here.
"""

from types import MappingProxyType

MI_SPECIALISTS = (
    MappingProxyType({"id": "MI-01", "name": "Ethan Hunt", "role": "Mission coordination", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-02", "name": "Luther Stickell", "role": "Defensive systems engineering", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-03", "name": "Benji Dunn", "role": "Gadget and communications design", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-04", "name": "Ilsa Faust", "role": "Risk and intelligence analysis", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-05", "name": "William Brandt", "role": "Strategic verification", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-06", "name": "Grace", "role": "Adaptive problem solving", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-07", "name": "Jane Carter", "role": "Operations planning", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-08", "name": "Eugene Kittridge", "role": "Governance analysis", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-09", "name": "Alan Hunley", "role": "Oversight review", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-10", "name": "Paris", "role": "Recovery planning", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-11", "name": "Nyah Nordoff-Hall", "role": "Negotiation analysis", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-12", "name": "Billy Baird", "role": "Transport logistics planning", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-13", "name": "Swanbeck", "role": "Mission briefing review", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
    MappingProxyType({"id": "MI-14", "name": "Sean Ambrose", "role": "Defensive adversarial analysis", "execution": "disabled", "provider": None, "tools": (), "authority": "none", "status": "design_approved"}),
)


def validate_mi_specialists():
    """Fail closed on duplicate identities or accidental execution grants."""
    ids = [agent["id"] for agent in MI_SPECIALISTS]
    names = [agent["name"] for agent in MI_SPECIALISTS]
    return (len(ids) == 14 and len(set(ids)) == 14
            and len(set(names)) == 14
            and all(agent["execution"] == "disabled"
                    and agent["provider"] is None
                    and not agent["tools"]
                    and agent["authority"] == "none"
                    for agent in MI_SPECIALISTS))
