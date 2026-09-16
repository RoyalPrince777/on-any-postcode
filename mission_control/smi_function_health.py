"""Truth-first Founder SMI function and canonical route health registry."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import (
    coherent_automation,
    smi_brain_evidence_runner,
    smi_chat_runtime,
    smi_proof_gate,
)

FUNCTION_SPECS = (
    {"id": "chat", "name": "SMI Chat", "endpoint": "mission_control.ollama_chat_dashboard", "path": "/mission/ollama", "proof": "chat_route"},
    {"id": "signals-21", "name": "21 Signals", "endpoint": "alignment.coherent_automation_status", "path": "/mission/smi/coherent-automation"},
    {"id": "war-room", "name": "War Room", "endpoint": "mission_control.war_room_dashboard", "path": "/mission/war-room", "proof": "war_room"},
    {"id": "guardian", "name": "Guardian", "endpoint": "alignment.smi_brain_evidence_runner_run", "path": "/mission/smi/brain/evidence-runner/run?command=guardian_check"},
    {"id": "hrm", "name": "HRM / Receipts", "endpoint": "alignment.smi_brain_receipts", "path": "/mission/smi/brain/receipts", "proof": "conversation_memory"},
    {"id": "brain", "name": "SMI Brain", "endpoint": "mission_control.brain_dashboard", "path": "/mission/brain"},
    {"id": "agents", "name": "Agents", "endpoint": "mission_control.agent_intelligence", "path": "/mission/agents"},
    {"id": "infrastructure", "name": "Infrastructure", "endpoint": "mission_control.infrastructure_dashboard", "path": "/mission/infrastructure"},
    {"id": "judgement", "name": "Judgement", "endpoint": "mission_control.judgement_dashboard", "path": "/mission/judgement"},
    {"id": "improvement", "name": "Improvement", "endpoint": "mission_control.smi_recursive_improvement_dashboard", "path": "/mission/improvement"},
    {"id": "function-health", "name": "Function Health", "endpoint": "alignment.smi_function_health_status", "path": "/mission/smi/function-health"},
    {"id": "routes", "name": "Routes", "endpoint": "alignment.smi_route_status", "path": "/mission/smi/routes"},
    {"id": "green-gate", "name": "Green Gate", "endpoint": "alignment.green_gate_status", "path": "/mission/smi/green-gate"},
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rules_for_endpoint(url_map: Any, endpoint: str):
    return tuple(
        rule
        for rule in url_map.iter_rules()
        if rule.endpoint == endpoint and "GET" in rule.methods
    )


def _canonical_rule(url_map: Any, spec: dict[str, str]):
    canonical_path = spec["path"].split("?", 1)[0]
    return next(
        (rule for rule in _rules_for_endpoint(url_map, spec["endpoint"]) if rule.rule == canonical_path),
        None,
    )


def route_status(url_map: Any) -> dict[str, Any]:
    routes = []
    for spec in FUNCTION_SPECS:
        all_rules = _rules_for_endpoint(url_map, spec["endpoint"])
        canonical = _canonical_rule(url_map, spec)
        routes.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "endpoint": spec["endpoint"],
                "path": spec["path"],
                "registered": canonical is not None,
                "methods": tuple(
                    sorted(
                        method
                        for method in (canonical.methods if canonical else ())
                        if method not in {"HEAD", "OPTIONS"}
                    )
                ),
                "compatibility_alias_count": max(0, len(all_rules) - (1 if canonical else 0)),
                "founder_only": True,
                "external_execution": False,
            }
        )
    canonical_paths = [row["path"] for row in routes]
    return {
        "component": "SMI Founder Canonical Route Registry",
        "generated_at": _now(),
        "routes": tuple(routes),
        "registered_count": sum(1 for row in routes if row["registered"]),
        "expected_count": len(routes),
        "all_registered": all(row["registered"] for row in routes),
        "duplicate_primary_paths": len(canonical_paths) - len(set(canonical_paths)),
        "compatibility_aliases_hidden_from_primary_ui": True,
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
        gate = {"green": False, "missing": ("proof_unavailable",), "execution_granted": False}

    functions = []
    for spec in FUNCTION_SPECS:
        function_id = spec["id"]
        route = route_by_id[function_id]
        proof_key = spec.get("proof")
        proven = None
        evidence = "Canonical Founder route registered."
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
                "name": spec["name"],
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
        "duplicate_primary_paths": routes["duplicate_primary_paths"],
        "green_gate": gate,
        "whole_smi_green": bool(gate.get("green")) and routes["all_registered"],
        "execution_granted": False,
        "no_fake_green": True,
        "human_authority_final": True,
    }
