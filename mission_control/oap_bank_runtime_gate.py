"""Governed runtime gate for the OAP Bank software surface.

This module decides what the installed OAP Bank may expose. It never grants
regulatory permission itself. Regulated capabilities require regulator
authorisation evidence, an effective permission scope and a passed production
gate. Customer-facing regulated execution remains disabled unless every owner
reports that the capability is allowed.
"""
from __future__ import annotations

from typing import Any

from . import (
    bank_authorisation,
    bank_authorisation_store,
    bank_permission_scope,
    oap_bank,
    prince_sovereign_bank,
    sika_pay_gateway,
    sika_production_evidence_store,
)

BANK_SURFACE_ID = "oap-bank-runtime-v1"


def capability_state(capability: str) -> dict[str, Any]:
    if capability not in bank_authorisation.REGULATED_CAPABILITIES:
        return {
            "capability": capability,
            "known": False,
            "enabled": False,
            "reason": "unknown_regulated_capability",
        }

    regulator = bank_authorisation_store.readiness_status()
    production = sika_production_evidence_store.readiness_status()
    regulator_proven = bool(regulator.get("authorised_bank"))
    production_passed = bool(production.get("production_gate_passed"))
    scope_allows = bool(bank_permission_scope.capability_allowed(capability))

    enabled = bank_authorisation.capability_allowed(
        capability,
        regulator_authorisation_proven=regulator_proven,
        production_gate_passed=production_passed,
        permission_scope_allows=scope_allows,
    )
    missing = []
    if not regulator_proven:
        missing.append("regulator_authorisation")
    if not scope_allows:
        missing.append("permission_scope")
    if not production_passed:
        missing.append("production_gate")

    return {
        "capability": capability,
        "known": True,
        "enabled": bool(enabled),
        "regulator_authorisation_proven": regulator_proven,
        "permission_scope_allows": scope_allows,
        "production_gate_passed": production_passed,
        "missing": tuple(missing),
    }


def runtime_status() -> dict[str, Any]:
    legacy = oap_bank.status()
    identity = prince_sovereign_bank.status()
    pay = sika_pay_gateway.status()
    capabilities = {
        item: capability_state(item)
        for item in sorted(bank_authorisation.REGULATED_CAPABILITIES)
    }

    regulated_enabled = any(
        row["enabled"] for row in capabilities.values()
    )

    return {
        "surface_id": BANK_SURFACE_ID,
        "name": identity["name"],
        "parent": identity["parent"],
        "installed_software_surface_ready": True,
        "regulated_bank_claim_enabled": False,
        "operational_bank": bool(regulated_enabled),
        "regulated_execution_enabled": bool(regulated_enabled),
        "deposit_taking_enabled": bool(
            capabilities["accept_deposits"]["enabled"]
        ),
        "payment_execution_enabled": bool(
            capabilities["execute_payments"]["enabled"]
        ),
        "bank_accounts_enabled": bool(
            capabilities["bank_accounts"]["enabled"]
        ),
        "payment_gateway_integrated": bool(pay["single_payment_door"]),
        "payment_gateway_requires_rights_record": bool(
            pay["rights_record_required"]
        ),
        "provider_calling": bool(pay["provider_calling"]),
        "settlement_execution": bool(pay["settlement_execution"]),
        "money_movement": bool(pay["money_movement"]),
        "legacy_bank_policy_preserved": legacy["bank_policy"],
        "capabilities": capabilities,
        "human_authority_final": True,
    }


def public_claims() -> dict[str, Any]:
    state = runtime_status()
    return {
        "may_claim_bank_software": True,
        "may_claim_regulated_bank": bool(state["regulated_bank_claim_enabled"]),
        "may_claim_deposit_taking": bool(state["deposit_taking_enabled"]),
        "may_claim_live_payments": bool(state["payment_execution_enabled"]),
        "may_claim_customer_bank_accounts": bool(state["bank_accounts_enabled"]),
        "must_disclose_software_only_when_locked": not bool(
            state["regulated_execution_enabled"]
        ),
    }
