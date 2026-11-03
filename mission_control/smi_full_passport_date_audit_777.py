"""Full-roster passport/date evidence audit. Never infer missing dates."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

DATE_FIELDS = ("created_at", "approved_at", "updated_at", "registered_at")


def audit_passports(agents: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Audit supplied canonical entries without creating identities or permissions."""
    entries = []
    seen_ids = set()
    seen_family_names = set()
    for agent in agents:
        agent_id = agent.get("agent_id")
        family = agent.get("family_id")
        name = agent.get("name")
        key = (family, name)
        duplicate_id = not isinstance(agent_id, str) or not agent_id or agent_id in seen_ids
        duplicate_identity = not family or not name or key in seen_family_names
        if agent_id:
            seen_ids.add(agent_id)
        seen_family_names.add(key)
        dates = {field: agent.get(field) or None for field in DATE_FIELDS}
        missing_dates = [field for field, value in dates.items() if value is None]
        entries.append({
            "agent_id": agent_id,
            "family": family,
            "name": name,
            "registry_status": agent.get("registry_status", "UNKNOWN"),
            "dates": dates,
            "missing_dates": missing_dates,
            "duplicate_id": duplicate_id,
            "duplicate_family_name": duplicate_identity,
            "identity_evidence_verified": False,
            "live_agent_verified": False,
        })
    return {
        "mode": "read_only_evidence_audit",
        "total_entries": len(entries),
        "missing_any_date": sum(bool(x["missing_dates"]) for x in entries),
        "duplicate_id_count": sum(x["duplicate_id"] for x in entries),
        "duplicate_family_name_count": sum(x["duplicate_family_name"] for x in entries),
        "dates_authenticated": False,
        "authority_changed": False,
        "overall_vpi": None,
        "entries": entries,
    }
