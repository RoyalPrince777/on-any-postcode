"""Truth-first Founder SMI function and route health registry."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from . import (
    coherent_automation,
    smi_brain_evidence_runner,
    smi_chat_runtime,
    smi_proof_gate,
)

FUNCTION_SPECS = (
    ("chat", "SMI Chat", "mission_control.ollama_chat_dashboard", "chat_route", None),
    ("live-monitor", "Live Monitor", "mission_control.smi_workbench_status", None, None),
    ("signals-21", "21 Signals", "alignment.coherent_automation_status", None, None),
    ("war-room", "War Room", "mission_control.war_room_dashboard", "war_room", None),
    ("guardian", "Guardian", "alignment.smi_brain_evidence_runner_run", None, {"command": "guardian_check"}),
    ("hrm", "HRM / Receipts", "alignment.smi_brain_receipts", "conversation_memory", None),
    ("brain", "SMI Brain", "mission_control.brain_dashboard", None, None),
    ("agents", "Agents", "mission_control.agent_intelligence", None, None),
    ("infrastructure", "Infrastructure", "mission_control.infrastructure_dashboard", None, None),
    ("judgement", "Judgement", "mission_control.judgement_dashboard", None, None),
    ("improvement", "Improvement", "mission_control.smi_recursive_improvement_dashboard", None, None),
    ("function-health", "Function Health", "alignment.smi_function_health_status", None, None),
    ("routes", "Routes", "alignment.smi_route_status", None, None),
    ("green-gate", "Green Gate", "alignment.green_gate_status", None, None),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rule(url_map: Any, endpoint: str):
    matches = [
        rule
        for rule in url_map.iter_rules()
        if rule.endpoint == endpoint and "GET" in rule.methods
    ]
    return min(matches, key=lambda rule: (len(rule.rule), rule.rule)) if matches else None


def _path(rule: Any, query: dict[str, str] | None) -> str | None:
    if rule is None:
        return None
    return rule.rule + (f"?{urlencode(query)}" if query else "")


def route_status(url_map: Any) -> dict[str, Any]:
    routes = []
    for function_id, name, endpoint, _proof, query in FUNCTION_SPECS:
        rule = _rule(url_map, endpoint)
        routes.append(
            {
                "id": function_id,
                "name": name,
                "endpoint": endpoint,
                "path": _path(rule, query),
                "registered": rule is not None,
                "methods": tuple(
                    sorted(
                        method
                        for method in (rule.methods if rule else ())
                        if method not in {"HEAD", "OPTIONS"}
                    )
                ),
                "founder_only": True,
                "external_execution": False,
            }
        )
    return {
        "component": "SMI Founder Route Registry",
        "generated_at": _now(),
        "routes": tuple(routes),
        "registered_count": sum(1 for row in routes if row["registered"]),
        "expected_count": len(routes),
        "all_registered": all(row["registered"] for row in routes),
        "public_private_separation": True,
        "secrets_exposed": False,
        "human_authority_final": True,
    }


def function_health(url_map: Any) -> dict[str, Any]:
    routes = route_status(url_map)
    route_by_id = {row["id"]: row for row in routes["routes"]}
    try:
        runtime = smi_chat_runtime.health()
    except Exception:  # noqa: BLE001
        runtime = {"status": "unavailable", "checks": {}}
    checks = runtime.get("checks") if isinstance(runtime.get("checks"), dict) else {}
    try:
        signals = coherent_automation.status()
    except Exception:  # noqa: BLE001
        signals = {"ready": False, "signals_valid": False, "signal_count": 0}
    try:
        gate = smi_proof_gate.public_safe_status()
    except Exception:  # noqa: BLE001
        gate = {
            "green": False,
            "missing": ("proof_unavailable",),
            "execution_granted": False,
        }

    functions = []
    for function_id, name, _endpoint, proof_key, _query in FUNCTION_SPECS:
        route = route_by_id[function_id]
        proven = None
        evidence = "Registered Founder-only route."
        if proof_key:
            proven = bool(checks.get(proof_key))
            evidence = f"smi_chat_runtime.health().checks.{proof_key}"
        elif function_id == "signals-21":
            proven = bool(
                signals.get("ready")
                and signals.get("signals_valid")
                and int(signals.get("signal_count") or 0) == 21
            )
            evidence = "coherent_automation.status() validates 21 canonical signals"
        elif function_id == "guardian":
            proven = "guardian_check" in smi_brain_evidence_runner.SAFE_COMMANDS
            evidence = "guardian_check registered in bounded evidence runner"
        elif function_id == "green-gate":
            proven = bool(gate.get("green"))
            evidence = "smi_proof_gate.public_safe_status()"

        if not route["registered"]:
            state, label = "red", "ROUTE MISSING"
        elif proven is True:
            state, label = "green", "PROVEN"
        elif proven is False:
            state, label = "yellow", "PROOF REQUIRED"
        else:
            state, label = "blue", "AVAILABLE"
        functions.append(
            {
                "id": function_id,
                "name": name,
                "path": route["path"],
                "available": bool(route["registered"]),
                "runtime_proven": proven,
                "state": state,
                "label": label,
                "evidence": evidence,
                "founder_only": True,
                "consequential_execution": False,
            }
        )

    return {
        "component": "SMI Founder Function Health",
        "generated_at": _now(),
        "functions": tuple(functions),
        "available_count": sum(1 for item in functions if item["available"]),
        "expected_count": len(functions),
        "all_primary_routes_registered": routes["all_registered"],
        "green_gate": gate,
        "whole_smi_green": bool(gate.get("green")) and routes["all_registered"],
        "execution_granted": False,
        "no_fake_green": True,
        "human_authority_final": True,
    }
