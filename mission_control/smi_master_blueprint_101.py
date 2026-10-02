"""Canonical SMI Full Master Blueprint 101 registry.

101 means architecture breadth, not 101 workflow stages. The registry composes
existing first-party SMI/OAP contracts and never grants execution, approval,
deployment, spending, dispatch, payment, permission changes or autonomy.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from . import (
    autonomy_levels,
    infrastructure,
    intelligence_lenses,
    smi_brain_protocol,
    smi_function_health,
)

COMMAND_CENTER_HOME_11: tuple[tuple[str, str], ...] = (
    ("home", "Home"),
    ("smi", "SMI"),
    ("signals", "Signals"),
    ("guardian", "Guardian"),
    ("war-room", "War Room"),
    ("intelligence", "Intelligence"),
    ("hrm-joog", "HRM / JOOG"),
    ("control", "Control"),
    ("incoming", "Incoming"),
    ("my-world", "My World"),
    ("settings", "Settings"),
)

GOVERNANCE_LOCKS_3: tuple[tuple[str, str], ...] = (
    ("human-authority-final", "Human Authority remains final"),
    ("no-unreviewed-consequential-execution", "No unreviewed consequential execution"),
    ("no-self-authority-expansion", "No self-permission or self-constitution expansion"),
)


def _row(
    *,
    item_id: str,
    name: str,
    category: str,
    owner: str,
    evidence_class: str,
    truth_state: str,
) -> dict[str, str]:
    return {
        "id": item_id,
        "name": name,
        "category": category,
        "owner": owner,
        "evidence_class": evidence_class,
        "truth_state": truth_state,
    }


def _registry() -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []

    rows.extend(
        _row(
            item_id=f"home.{item_id}",
            name=name,
            category="command_center_home",
            owner="SMI Command Center",
            evidence_class="source_and_regression_contract",
            truth_state="implemented",
        )
        for item_id, name in COMMAND_CENTER_HOME_11
    )

    rows.extend(
        _row(
            item_id=f"mission.{index:02d}",
            name=str(name),
            category="mission_links",
            owner="SMI Mission Loop",
            evidence_class="canonical_protocol_contract",
            truth_state="implemented",
        )
        for index, name in enumerate(smi_brain_protocol.MAJOR_LINKS_7, start=1)
    )

    rows.extend(
        _row(
            item_id=f"function.{spec['id']!s}",
            name=str(spec["name"]),
            category="core_functions",
            owner="SMI Function Health",
            evidence_class="registered_route_plus_runtime_proof",
            truth_state="evidence_driven",
        )
        for spec in smi_function_health.FUNCTION_SPECS
    )

    rows.extend(
        _row(
            item_id=f"signal.{index:02d}",
            name=str(name),
            category="core_review_signals",
            owner="SMI Live Brain",
            evidence_class="request_specific_review_signal",
            truth_state="evidence_driven",
        )
        for index, name in enumerate(
            smi_brain_protocol.CORE_REVIEW_SIGNALS_21, start=1
        )
    )

    rows.extend(
        _row(
            item_id=f"lens.{lens_id}",
            name=str(intelligence_lenses.LENS_BY_ID[lens_id]["name"]),
            category="intelligence_lenses",
            owner="SMI Intelligence Router",
            evidence_class="analysis_contract",
            truth_state="implemented",
        )
        for lens_id in intelligence_lenses.FULL_LENS_IDS
    )

    rows.extend(
        _row(
            item_id=f"interaction.{spec['id']!s}",
            name=str(spec["name"]),
            category="interaction_surfaces",
            owner="Personal SMI",
            evidence_class="implementation_plus_independent_live_proof",
            truth_state="certification_required",
        )
        for spec in smi_function_health.INTERACTION_CERTIFICATION_SPECS
    )

    rows.extend(
        _row(
            item_id=f"autonomy.{level.lower()}",
            name=f"{level} · {name}",
            category="autonomy_levels",
            owner="SMI Autonomy Constitution",
            evidence_class="governance_and_runtime_proof",
            truth_state=(
                "supported"
                if level in {"A1", "A2"}
                else "bounded"
                if level in {"A3", "A4"}
                else "locked"
            ),
        )
        for level, name in autonomy_levels.AUTONOMY_LEVELS.items()
    )

    rows.extend(
        _row(
            item_id=f"infrastructure.{module['id']!s}",
            name=str(module["name"]),
            category="infrastructure_modules",
            owner="OAP Infrastructure",
            evidence_class="runtime_delivery_evidence",
            truth_state="runtime_proof_required",
        )
        for module in infrastructure.LOCKED_INFRASTRUCTURE_MODULES
    )

    rows.extend(
        _row(
            item_id=f"governance.{item_id}",
            name=name,
            category="governance_locks",
            owner="Human Authority / Guardian",
            evidence_class="constitutional_boundary",
            truth_state="locked_boundary",
        )
        for item_id, name in GOVERNANCE_LOCKS_3
    )

    return tuple(rows)


MASTER_BLUEPRINT_101 = _registry()
EXPECTED_CATEGORY_COUNTS = {
    "command_center_home": 11,
    "mission_links": 7,
    "core_functions": 13,
    "core_review_signals": 21,
    "intelligence_lenses": 26,
    "interaction_surfaces": 9,
    "autonomy_levels": 7,
    "infrastructure_modules": 4,
    "governance_locks": 3,
}


def validate() -> dict[str, Any]:
    ids = tuple(item["id"] for item in MASTER_BLUEPRINT_101)
    names = tuple(item["name"] for item in MASTER_BLUEPRINT_101)
    category_counts = Counter(item["category"] for item in MASTER_BLUEPRINT_101)
    errors: list[str] = []
    if len(MASTER_BLUEPRINT_101) != 101:
        errors.append("blueprint_item_count_must_equal_101")
    if len(ids) != len(set(ids)):
        errors.append("duplicate_blueprint_ids")
    if any(not name.strip() for name in names):
        errors.append("blank_blueprint_name")
    if dict(category_counts) != EXPECTED_CATEGORY_COUNTS:
        errors.append("blueprint_category_counts_changed")
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "item_count": len(MASTER_BLUEPRINT_101),
        "unique_id_count": len(set(ids)),
        "category_counts": dict(category_counts),
        "expected_category_counts": dict(EXPECTED_CATEGORY_COUNTS),
        "progress_stage_count": 0,
        "is_progress_ladder": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    validation = validate()
    return {
        "component": "SMI Full Master Blueprint 101",
        "purpose": "architecture breadth and ownership map",
        "item_count": len(MASTER_BLUEPRINT_101),
        "items": MASTER_BLUEPRINT_101,
        "validation": validation,
        "protocol": {
            "101_is_architecture_breadth": True,
            "101_is_progress_stages": False,
            "unnecessary_stages_removed": True,
            "repeated_status_loops_removed": True,
            "demos_as_progress_removed": True,
            "simulation_when_real_proof_exists_removed": True,
            "duplicate_reports_removed": True,
            "repeated_approval_prompts_removed": True,
            "cosmetic_percentage_inflation_removed": True,
            "stop_after_every_small_fix_removed": True,
        },
        "authority": {
            "execution_granted": False,
            "approval_granted": False,
            "autonomy_expanded": False,
            "human_authority_final": True,
        },
    }
