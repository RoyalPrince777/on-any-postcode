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


def validate_mi_specialists(specialists=None):
    """Reject malformed identities, unexpected grants and roster drift."""
    roster = MI_SPECIALISTS if specialists is None else tuple(specialists)
    if len(roster) != 14:
        return False
    try:
        ids = [agent["id"] for agent in roster]
        names = [agent["name"] for agent in roster]
        return (
            set(ids) == {f"MI-{number:02d}" for number in range(1, 15)}
            and len(set(names)) == 14
            and all(
                isinstance(agent["name"], str) and bool(agent["name"].strip())
                and isinstance(agent["role"], str) and bool(agent["role"].strip())
                and agent["status"] == "design_approved"
                and agent["execution"] == "disabled"
                and agent["provider"] is None
                and agent["tools"] == ()
                and agent["authority"] == "none"
                and set(agent) == {"id", "name", "role", "status", "execution", "provider", "tools", "authority"}
                for agent in roster
            )
        )
    except (KeyError, TypeError, ValueError):
        return False
