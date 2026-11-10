"""Unified OAP commerce install/readiness orchestration.

Applies only first-party schemas after explicit Human Authority approval.
Provider secrets remain deployment-only environment variables.
"""
from __future__ import annotations

from . import (
    commerce_provider_receipts,
    distribution_runtime,
    founder_private_pod_orders,
    market_supplier_network,
    sika_payment_orchestrator,
    sika_payment_submission_evidence,
    sika_secure_provider_runtime,
)

COMPONENTS = (
    ("supplier_network", market_supplier_network.init_schema),
    ("payment_orchestrator", sika_payment_orchestrator.init_schema),
    ("payment_submission_evidence", sika_payment_submission_evidence.init_schema),
    ("distribution_runtime", distribution_runtime.init_schema),
    ("provider_receipts", commerce_provider_receipts.init_schema),
    ("founder_private_pod_orders", founder_private_pod_orders.init_schema),
)


def install(*, assume_yes: bool = False, dry_run: bool = True) -> dict[str, object]:
    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    results: dict[str, object] = {}
    all_ready = True
    for name, init in COMPONENTS:
        result = init(assume_yes=True, dry_run=dry_run)
        results[name] = result
        if not dry_run and result.get("schema_ready") is not True:
            all_ready = False
    return {
        "system": "OAP Commerce Installer",
        "dry_run": dry_run,
        "components": results,
        "schema_ready": (False if dry_run else all_ready),
        "payment_provider": sika_secure_provider_runtime.configuration_status("payment"),
        "pod_provider": sika_secure_provider_runtime.configuration_status("pod"),
        "secrets_source": "environment_only",
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    payment = sika_secure_provider_runtime.configuration_status("payment")
    pod = sika_secure_provider_runtime.configuration_status("pod")
    return {
        "system": "OAP Commerce Install Readiness",
        "installer_built": True,
        "schema_components": [name for name, _ in COMPONENTS],
        "provider_runtime_built": True,
        "payment_provider_configured": payment["configuration_complete"],
        "pod_provider_configured": pod["configuration_complete"],
        "environment_only_secrets": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }
