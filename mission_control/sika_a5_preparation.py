"""SIKA A5 governed-preparation pack.

Read-only preparation evidence. It never enables A6/A7 or regulated execution.
"""
from __future__ import annotations

from typing import Any

from . import autonomy_levels, sika_intelligence, sika_payment_licence_gate, sika_safety


def pack() -> dict[str, Any]:
    install = sika_safety.install_readiness()
    licence = sika_payment_licence_gate.status()
    bank = sika_intelligence.bank_intelligence()
    prepared = {
        "PROOF_PACK": True,
        "ROLLBACK_PLAN": True,
        "DEPLOY_PLAN": True,
        "GAP_ANALYSIS": True,
        "WAR_ROOM_PACK": True,
    }
    return {
        "level": "A5",
        "name": autonomy_levels.AUTONOMY_LEVELS["A5"],
        "preparation_only": True,
        "preparation_actions": prepared,
        "software_evidence": {
            "private_software_acceptance_ready": install["private_software_acceptance_ready"],
            "public_pwa_software_ready": install["public_pwa_software_ready"],
            "fraud_preflight": install["fraud_preflight"],
            "regulated_execution_fail_closed": install["regulated_execution_fail_closed"],
            "bank_intelligence_read_only": bank["read_only"],
        },
        "rollback_plan": {
            "preserve_previous_render_deploy": True,
            "no_database_migration": True,
            "no_customer_funds": True,
            "no_payment_execution": True,
            "rollback_target": "last independently verified live SIKA acceptance head",
        },
        "deploy_plan": {
            "candidate_then_ci_then_isolated_acceptance": True,
            "merge_requires_human_authority": True,
            "production_deploy_requires_human_authority": True,
            "post_deploy_live_acceptance_required": True,
        },
        "gaps": {
            "payment_licence_evidence_complete": licence["licence_evidence_complete"],
            "physical_android_acceptance": install["real_android_pwa_acceptance"],
            "native_android_package": install["native_android_package_ready"],
            "production_merge": False,
            "production_deploy": False,
        },
        "war_room": {
            "guardian_required": True,
            "green_gate_required": True,
            "hrm_receipts_required": True,
            "human_authority_final": True,
        },
        "a6_execution_granted": False,
        "a7_enabled": False,
        "payment_execution_enabled": False,
        "self_permission_change_allowed": False,
    }
