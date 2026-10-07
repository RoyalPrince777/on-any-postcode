"""First-party POD provider registry for OAP Market.

Routes one governed POD request to one explicitly selected provider while
keeping provider credentials, execution switches, and trust boundaries
independent. Tapstitch remains fail-closed until its direct API contract is
proven.
"""
from __future__ import annotations

import os

from . import printful_pod_adapter, prodigi_pod_adapter, tapstitch_pod_connector

SUPPORTED_PROVIDERS = ("prodigi", "printful", "tapstitch")


class PodProviderRegistryError(RuntimeError):
    """Safe registry error without provider credential material."""


def _legacy_provider_id() -> str:
    return str(os.environ.get("OAP_POD_PROVIDER_ID", "") or "").strip().lower()


def resolve_provider_id(value: object = None) -> str:
    provider_id = str(value or "").strip().lower()
    if not provider_id:
        provider_id = _legacy_provider_id()
    if provider_id not in SUPPORTED_PROVIDERS:
        raise PodProviderRegistryError("pod_provider_not_supported")
    return provider_id


def status() -> dict[str, object]:
    providers: dict[str, dict[str, object]] = {
        "prodigi": prodigi_pod_adapter.status(),
        "printful": printful_pod_adapter.status(),
        "tapstitch": tapstitch_pod_connector.status(),
    }
    return {
        "registry": "oap_pod_multi_provider",
        "supported_providers": list(SUPPORTED_PROVIDERS),
        "providers": providers,
        "single_global_provider_required": False,
        "per_order_provider_routing_supported": True,
        "tapstitch_direct_execution_allowed": False,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def submit(
    *,
    provider_id: object,
    payload: object,
    idempotency_key: object,
) -> dict[str, object]:
    selected = resolve_provider_id(provider_id)
    if not isinstance(payload, dict):
        raise PodProviderRegistryError("pod_provider_payload_required")

    if selected == "prodigi":
        return prodigi_pod_adapter.submit_order(
            payload=dict(payload),
            idempotency_key=idempotency_key,
        )
    if selected == "printful":
        return printful_pod_adapter.create_draft_order(
            payload=dict(payload),
            idempotency_key=idempotency_key,
        )

    tapstitch_pod_connector.assert_external_execution_allowed()
    raise PodProviderRegistryError("tapstitch_direct_execution_unavailable")
