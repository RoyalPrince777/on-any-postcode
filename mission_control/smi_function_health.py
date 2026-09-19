"""Truth-first Founder SMI function and canonical route health registry."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import (
    agents,
    brain,
    coherent_automation,
    infrastructure,
    judgement,
    smi_brain_evidence_runner,
    smi_chat_runtime,
    smi_proof_gate,
    smi_recursive_improvement,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

INTERACTION_CERTIFICATION_SPECS = (
    {
        "id": "chat",
        "name": "SMI Chat",
        "markers": ("chat-mode-button", "streamUrl"),
        "backend": "governed SMI stream",
    },
    {
        "id": "voice",
        "name": "SMI Voice",
        "markers": ("voice-mode-button", "mic-button"),
        "backend": "speech capture → governed SMI stream",
    },
    {
        "id": "vision",
        "name": "SMI Vision",
        "markers": ("vision-button", "SMI Vision camera capture"),
        "backend": "image_data → governed SMI stream",
    },
    {
        "id": "face-up",
        "name": "Face Up",
        "markers": ("faceup-button", "getUserMedia", "faceup-capture"),
        "backend": "local camera/mic + bounded frame → Vision path",
        "known_gap": "continuous live SMI video participation is not certified",
    },
    {
        "id": "screen",
        "name": "Screen Intelligence",
        "markers": ("screen-button", "getDisplayMedia", "Screen Intelligence capture"),
        "backend": "bounded frame → Vision path",
    },
    {
        "id": "tools",
        "name": "Plus / Tools",
        "markers": ("tools-mode-button", "plus-button"),
        "backend": "existing governed tool and connector routes",
    },
    {
        "id": "intelligence-selector",
        "name": "Intelligence Selector",
        "markers": (
            '["manual", "Manual"]',
            '["instant", "3"]',
            '["think", "7"]',
            '["deep_dive", "21"]',
            '["war_room", "War Room"]',
        ),
        "backend": "Auto / Manual / 3 / 7 / 21 / War Room governed routing",
    },
    {
        "id": "runtime-controls",
        "name": "Runtime Controls",
        "markers": ("pause-button", "stop-button"),
        "backend": "client display pause/resume + governed stream cancellation on Stop",
    },
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


def _percent(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((count / total) * 100.0, 1)


def _safe_read(
    reader: Callable[[], Mapping[str, Any]],
    fallback: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    try:
        value = reader()
    except Exception:  # noqa: BLE001 - Function Health must fail closed, not fail open.
        return dict(fallback), False
    if not isinstance(value, Mapping):
        return dict(fallback), False
    return dict(value), True


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
    registered_count = sum(1 for row in routes if row["registered"])
    expected_count = len(routes)
    return {
        "component": "SMI Founder Canonical Route Registry",
        "generated_at": _now(),
        "routes": tuple(routes),
        "registered_count": registered_count,
        "expected_count": expected_count,
        "availability_percent": _percent(registered_count, expected_count),
        "all_registered": all(row["registered"] for row in routes),
        "duplicate_primary_paths": len(canonical_paths) - len(set(canonical_paths)),
        "compatibility_aliases_hidden_from_primary_ui": True,
        "public_private_separation": True,
        "secrets_exposed": False,
        "human_authority_final": True,
    }


def interaction_certification() -> dict[str, Any]:
    """Track SMI interaction implementation separately from live Green Gate proof."""

    try:
        base = (
            _REPOSITORY_ROOT / "mission_control" / "templates" / "ollama_chat_base.html"
        ).read_text(encoding="utf-8")
        wrapper = (
            _REPOSITORY_ROOT / "mission_control" / "templates" / "ollama_chat.html"
        ).read_text(encoding="utf-8")
        script = (
            _REPOSITORY_ROOT / "mission_control" / "static" / "smi_interaction_layer.js"
        ).read_text(encoding="utf-8")
        source = f"{base}\n{wrapper}\n{script}"
        source_available = True
    except OSError:
        source = ""
        source_available = False

    surfaces = []
    for spec in INTERACTION_CERTIFICATION_SPECS:
        markers = tuple(str(item) for item in spec["markers"])
        wired = bool(source_available and all(marker in source for marker in markers))
        surfaces.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "implementation_wired": wired,
                "backend_path": spec["backend"],
                "known_gap": spec.get("known_gap"),
                "live_runtime_proven": False,
                "state": "purple" if wired else "red",
                "label": "CERTIFICATION REQUIRED" if wired else "IMPLEMENTATION MISSING",
            }
        )

    implemented_count = sum(
        1 for item in surfaces if item["implementation_wired"]
    )
    expected_count = len(surfaces)
    return {
        "component": "SMI Interaction Certification",
        "generated_at": _now(),
        "surfaces": tuple(surfaces),
        "implemented_count": implemented_count,
        "expected_count": expected_count,
        "implementation_percent": _percent(implemented_count, expected_count),
        "all_implemented_for_certification": implemented_count == expected_count,
        "whole_interaction_green": False,
        "live_proof_required": True,
        "proof_chain": (
            "control",
            "ui_action",
            "governed_backend",
            "correct_result",
            "failure_handling",
            "audit_where_required",
            "independent_verification",
            "green_gate",
        ),
        "no_fake_green": True,
        "human_authority_final": True,
    }


def function_health(url_map: Any) -> dict[str, Any]:
    """Evaluate every primary Founder function with an explicit evidence source.

    Function operability and whole-system Green Gate readiness remain separate.
    A working proof reader never upgrades missing receipts, observability or external
    evidence into a fake whole-SMI green state.
    """

    routes = route_status(url_map)
    route_by_id = {row["id"]: row for row in routes["routes"]}

    runtime, runtime_checked = _safe_read(
        smi_chat_runtime.health,
        {"status": "unavailable", "checks": {}},
    )
    checks = runtime.get("checks") if isinstance(runtime.get("checks"), dict) else {}
    signals, signals_checked = _safe_read(
        coherent_automation.status,
        {"ready": False, "signals_valid": False, "signal_count": 0},
    )
    gate, gate_checked = _safe_read(
        smi_proof_gate.public_safe_status,
        {
            "green": False,
            "missing": ("proof_unavailable",),
            "execution_granted": False,
        },
    )
    brain_status, brain_checked = _safe_read(
        brain.get_public_brain_status,
        {"validation": {"passed": False}, "brain_count": 0},
    )
    agent_status, agents_checked = _safe_read(
        agents.validate_agent_registry,
        {"passed": False, "registry_complete": False},
    )
    infrastructure_status, infrastructure_checked = _safe_read(
        infrastructure.get_public_infrastructure,
        {"validation": {"passed": False}},
    )
    judgement_status, judgement_checked = _safe_read(
        judgement.status,
        {"schema_ready": False, "ready": False, "error": "unavailable"},
    )
    improvement_status, improvement_checked = _safe_read(
        smi_recursive_improvement.run_cycle,
        {
            "light": "orange",
            "proof": {"live_cycle_ran": False},
            "consequential_action": False,
        },
    )

    brain_validation = brain_status.get("validation")
    if not isinstance(brain_validation, Mapping):
        brain_validation = {}
    infrastructure_validation = infrastructure_status.get("validation")
    if not isinstance(infrastructure_validation, Mapping):
        infrastructure_validation = {}
    improvement_proof = improvement_status.get("proof")
    if not isinstance(improvement_proof, Mapping):
        improvement_proof = {}

    route_integrity = bool(
        routes["all_registered"] and routes["duplicate_primary_paths"] == 0
    )

    proofs: dict[str, dict[str, Any]] = {
        "signals-21": {
            "checked": bool(
                signals_checked
                and {"ready", "signals_valid", "signal_count"}.issubset(signals)
            ),
            "ready": bool(
                signals.get("ready")
                and signals.get("signals_valid")
                and int(signals.get("signal_count") or 0) == 21
            ),
            "evidence": "coherent_automation.status() validates 21 canonical signals",
        },
        "guardian": {
            "checked": True,
            "ready": "guardian_check" in smi_brain_evidence_runner.SAFE_COMMANDS,
            "evidence": "guardian_check registered in bounded evidence runner",
        },
        "brain": {
            "checked": bool(brain_checked and "passed" in brain_validation),
            "ready": bool(
                brain_validation.get("passed")
                and int(brain_status.get("brain_count") or 0) == 1
            ),
            "evidence": "brain.get_public_brain_status() validates one governed SMI brain",
        },
        "agents": {
            "checked": bool(agents_checked and "passed" in agent_status),
            "ready": bool(
                agent_status.get("passed") and agent_status.get("registry_complete")
            ),
            "evidence": "agents.validate_agent_registry() validates the canonical registry",
        },
        "infrastructure": {
            "checked": bool(
                infrastructure_checked and "passed" in infrastructure_validation
            ),
            "ready": bool(infrastructure_validation.get("passed")),
            "evidence": "infrastructure.get_public_infrastructure().validation",
        },
        "judgement": {
            "checked": bool(judgement_checked and "schema_ready" in judgement_status),
            "ready": bool(
                judgement_status.get("schema_ready")
                and not judgement_status.get("error")
            ),
            "evidence": "judgement.status() verifies the governed decision ledger schema",
        },
        "improvement": {
            "checked": bool(
                improvement_checked and "live_cycle_ran" in improvement_proof
            ),
            "ready": bool(
                improvement_proof.get("live_cycle_ran")
                and improvement_status.get("consequential_action") is False
            ),
            "evidence": "smi_recursive_improvement.run_cycle() executes a read-only live evidence review",
        },
        "function-health": {
            "checked": True,
            "ready": route_integrity,
            "evidence": "Function Health generated this truth-labelled 13-function projection",
        },
        "routes": {
            "checked": True,
            "ready": route_integrity,
            "evidence": "Canonical route registry is complete and duplicate-free",
        },
        "green-gate": {
            "checked": bool(gate_checked and "green" in gate),
            "ready": bool(gate.get("green")),
            "evidence": "smi_proof_gate.public_safe_status()",
        },
    }

    for function_id, proof_key in (
        ("chat", "chat_route"),
        ("war-room", "war_room"),
        ("hrm", "conversation_memory"),
    ):
        proofs[function_id] = {
            "checked": bool(runtime_checked and proof_key in checks),
            "ready": bool(checks.get(proof_key)),
            "evidence": f"smi_chat_runtime.health().checks.{proof_key}",
        }

    functions = []
    for spec in FUNCTION_SPECS:
        function_id = spec["id"]
        route = route_by_id[function_id]
        proof = proofs[function_id]
        proof_checked = bool(proof["checked"])
        runtime_proven = bool(proof["ready"])

        if not route["registered"]:
            state, label = "red", "ROUTE MISSING"
        elif not proof_checked:
            state, label = "yellow", "EVIDENCE UNAVAILABLE"
        elif runtime_proven:
            state, label = "green", "PROVEN"
        else:
            state, label = "yellow", "PROOF REQUIRED"

        functions.append(
            {
                "id": function_id,
                "name": spec["name"],
                "path": route["path"],
                "available": bool(route["registered"]),
                "proof_checked": proof_checked,
                "runtime_proven": runtime_proven,
                "state": state,
                "label": label,
                "evidence": proof["evidence"],
                "founder_only": True,
                "consequential_execution": False,
            }
        )

    expected_count = len(functions)
    available_count = sum(1 for item in functions if item["available"])
    proof_checked_count = sum(1 for item in functions if item["proof_checked"])
    runtime_ready_count = sum(1 for item in functions if item["runtime_proven"])
    whole_smi_green = bool(
        gate.get("green")
        and route_integrity
        and runtime_ready_count == expected_count
    )

    return {
        "component": "SMI Founder Function Health",
        "generated_at": _now(),
        "functions": tuple(functions),
        "available_count": available_count,
        "expected_count": expected_count,
        "availability_percent": _percent(available_count, expected_count),
        "proof_checked_count": proof_checked_count,
        "proof_coverage_percent": _percent(proof_checked_count, expected_count),
        "runtime_ready_count": runtime_ready_count,
        "runtime_ready_percent": _percent(runtime_ready_count, expected_count),
        "proof_required_count": expected_count - runtime_ready_count,
        "all_proof_sources_checked": proof_checked_count == expected_count,
        "all_primary_routes_registered": routes["all_registered"],
        "duplicate_primary_paths": routes["duplicate_primary_paths"],
        "green_gate": gate,
        "interaction_certification": interaction_certification(),
        "whole_smi_green": whole_smi_green,
        "readiness_scope": "Founder function operability; universal external-world readiness is measured separately",
        "execution_granted": False,
        "no_fake_green": True,
        "human_authority_final": True,
    }
