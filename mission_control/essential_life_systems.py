"""First-party Essential Life Systems registry for OAP resilience.

This module is intentionally evidence-bounded. It defines the systems,
dependencies, monitor schema and OAP surface responsibilities, but it never
claims live external telemetry is connected unless a caller provides it.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

SYSTEMS: tuple[dict[str, object], ...] = (
    {"id":"air","name":"Air","band":"life","monitors":("quality","ventilation","pollution","alerts"),"depends_on":()},
    {"id":"water","name":"Water","band":"life","monitors":("supply","quality","outages","reserves"),"depends_on":("energy",)},
    {"id":"food","name":"Food","band":"life","monitors":("availability","supply_routes","shortage_risk","waste_risk"),"depends_on":("water","energy","movement")},
    {"id":"health","name":"Health","band":"body","monitors":("service_availability","demand","capacity","critical_supplies"),"depends_on":("water","food","energy","communication","movement","sanitation")},
    {"id":"shelter","name":"Shelter","band":"home","monitors":("availability","occupancy","building_status","emergency_capacity"),"depends_on":("energy","water","sanitation","safety")},
    {"id":"sanitation","name":"Sanitation","band":"home","monitors":("waste","sewage","collection","contamination_risk"),"depends_on":("water","energy","movement")},
    {"id":"energy","name":"Energy","band":"power","monitors":("supply","load","backup","outages"),"depends_on":()},
    {"id":"communication","name":"Communication","band":"connect","monitors":("network","esim","internet","radio"),"depends_on":("energy",)},
    {"id":"movement","name":"Movement","band":"move","monitors":("roads","transport","logistics","route_disruption"),"depends_on":("energy","communication")},
    {"id":"safety","name":"Safety","band":"protect","monitors":("incidents","hazards","response","recovery"),"depends_on":("communication","movement","energy")},
)

BANDS: tuple[dict[str, object], ...] = (
    {"id":"life","name":"Life","systems":("air","water","food")},
    {"id":"body","name":"Body","systems":("health",)},
    {"id":"home","name":"Home","systems":("shelter","sanitation")},
    {"id":"power","name":"Power","systems":("energy",)},
    {"id":"connect","name":"Connect","systems":("communication",)},
    {"id":"move","name":"Move","systems":("movement",)},
    {"id":"protect","name":"Protect","systems":("safety",)},
)

SMI_VIEWS = ("Now", "Next", "Recover")
INTELLIGENCE_LOOP = ("Monitor", "Understand", "Predict", "Protect", "Respond", "Recover", "Learn")

SURFACE_ROLES: tuple[dict[str, str], ...] = (
    {"surface":"Library","role":"Know"},
    {"surface":"Academy","role":"Learn & Do"},
    {"surface":"Organiser","role":"Manage"},
    {"surface":"World","role":"Locate & Explore"},
    {"surface":"LAB","role":"Research & Improve"},
    {"surface":"SMI","role":"Understand Dependencies"},
    {"surface":"Guardian","role":"Protect"},
    {"surface":"Control Center","role":"Operate"},
    {"surface":"My World","role":"Store Personal State"},
)

MONITOR_TYPES = (
    "status_cards",
    "trend_graphs",
    "dependency_graph",
    "map_layers",
    "capacity",
    "backups",
    "incident_timeline",
    "recovery",
    "risk_heatmap",
    "guardian_alerts",
)

def _system_lookup() -> dict[str, dict[str, object]]:
    return {str(item["id"]): dict(item) for item in SYSTEMS}


def validate_registry() -> dict[str, object]:
    ids = [str(item["id"]) for item in SYSTEMS]
    bands = [str(item["id"]) for item in BANDS]
    errors: list[str] = []
    if len(ids) != 10 or len(set(ids)) != 10:
        errors.append("Exactly ten unique essential systems are required")
    if len(bands) != 7 or len(set(bands)) != 7:
        errors.append("Exactly seven unique resilience bands are required")
    system_ids = set(ids)
    for item in SYSTEMS:
        if item["band"] not in set(bands):
            errors.append(f"Unknown band for {item['id']}")
        if any(dep not in system_ids or dep == item["id"] for dep in item["depends_on"]):
            errors.append(f"Invalid dependency for {item['id']}")
        if not item["monitors"]:
            errors.append(f"Missing monitors for {item['id']}")
    band_members = [sid for band in BANDS for sid in band["systems"]]
    if set(band_members) != system_ids or len(band_members) != len(system_ids):
        errors.append("Every system must appear in exactly one resilience band")
    if SMI_VIEWS != ("Now", "Next", "Recover"):
        errors.append("SMI views drifted")
    if INTELLIGENCE_LOOP != ("Monitor","Understand","Predict","Protect","Respond","Recover","Learn"):
        errors.append("Intelligence loop drifted")
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "systems": len(SYSTEMS),
        "bands": len(BANDS),
        "monitor_types": len(MONITOR_TYPES),
        "live_telemetry_claimed": False,
    }


def dependency_edges() -> tuple[dict[str, str], ...]:
    edges: list[dict[str, str]] = []
    for item in SYSTEMS:
        for dep in item["depends_on"]:
            edges.append({"source": str(dep), "target": str(item["id"])})
    return tuple(edges)


def reverse_dependencies() -> dict[str, tuple[str, ...]]:
    reverse: dict[str, list[str]] = defaultdict(list)
    for edge in dependency_edges():
        reverse[edge["source"]].append(edge["target"])
    return {key: tuple(sorted(value)) for key, value in reverse.items()}


def system_snapshot(system_id: str) -> dict[str, Any]:
    item = _system_lookup().get(str(system_id).strip().casefold())
    if item is None:
        raise ValueError("unknown_essential_system")
    return {
        **item,
        "status": "unverified",
        "evidence_state": "registry_only",
        "live_telemetry": False,
        "downstream": reverse_dependencies().get(str(item["id"]), ()),
    }


def smi_snapshot() -> dict[str, object]:
    validation = validate_registry()
    return {
        "name": "Essential Life Systems",
        "truth_mode": True,
        "status": "registry_ready" if validation["passed"] else "blocked",
        "views": SMI_VIEWS,
        "intelligence_loop": INTELLIGENCE_LOOP,
        "bands": BANDS,
        "systems": tuple(system_snapshot(str(item["id"])) for item in SYSTEMS),
        "dependency_edges": dependency_edges(),
        "monitor_types": MONITOR_TYPES,
        "surface_roles": SURFACE_ROLES,
        "live_telemetry": False,
        "validation": validation,
    }
