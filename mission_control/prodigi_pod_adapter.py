"""Prodigi POD adapter for OAP Supplier Bridge.

Provider-specific transport only. OAP remains the order owner and authority.
Secrets are environment-only. Sandbox is the default-safe target.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any
from urllib import error, parse, request

_MAX_REQUEST_BYTES = 64 * 1024
_MAX_RESPONSE_BYTES = 128 * 1024
_TIMEOUT_SECONDS = 12


class ProdigiAdapterError(RuntimeError):
    """Safe adapter error without credential material."""


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _env(name: str) -> str:
    return str(os.environ.get(name, "") or "").strip()


def _provider_env(specific: str, legacy: str) -> str:
    value = _env(specific)
    if value:
        return value
    if _env("OAP_POD_PROVIDER_ID").lower() == "prodigi":
        return _env(legacy)
    return ""


def _enabled() -> bool:
    return _provider_env(
        "OAP_POD_PRODIGI_EXECUTION_ENABLED",
        "OAP_POD_PROVIDER_EXECUTION_ENABLED",
    ).lower() in {"1", "true", "yes", "on"}


def _config() -> dict[str, object]:
    provider_id = "prodigi"
    base_url = _provider_env(
        "OAP_POD_PRODIGI_BASE_URL", "OAP_POD_PROVIDER_BASE_URL"
    ).rstrip("/")
    allowed_host = _provider_env(
        "OAP_POD_PRODIGI_ALLOWED_HOST", "OAP_POD_PROVIDER_ALLOWED_HOST"
    ).lower()
    api_key = _provider_env(
        "OAP_POD_PRODIGI_TOKEN", "OAP_POD_PROVIDER_TOKEN"
    )
    parsed = parse.urlparse(base_url) if base_url else None
    host = str(parsed.hostname or "").lower() if parsed else ""
    sandbox = host == "api.sandbox.prodigi.com"
    live = host == "api.prodigi.com"
    if _enabled():
        if not base_url or parsed is None or parsed.scheme != "https":
            raise ProdigiAdapterError("prodigi_https_required")
        if host != allowed_host:
            raise ProdigiAdapterError("prodigi_host_not_allowed")
        if not (sandbox or live):
            raise ProdigiAdapterError("prodigi_host_unrecognised")
        if not api_key:
            raise ProdigiAdapterError("prodigi_api_key_missing")
    return {
        "provider_id": provider_id,
        "base_url": base_url,
        "allowed_host": allowed_host,
        "api_key": api_key,
        "sandbox": sandbox,
        "live": live,
        "enabled": _enabled(),
    }


def status() -> dict[str, object]:
    config = _config()
    return {
        "adapter": "prodigi",
        "provider_id_present": config["provider_id"] == "prodigi",
        "base_url_present": bool(config["base_url"]),
        "api_key_present": bool(config["api_key"]),
        "allowed_host_present": bool(config["allowed_host"]),
        "sandbox": bool(config["sandbox"]),
        "live": bool(config["live"]),
        "execution_enabled": bool(config["enabled"]),
        "configuration_complete": all((
            config["base_url"],
            config["api_key"],
            config["allowed_host"],
            config["enabled"],
            config["sandbox"] or config["live"],
        )),
        "auth_scheme": "X-API-Key",
        "signed_callback_trusted": False,
        "status_readback_supported": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def _url(path: str) -> tuple[dict[str, object], str]:
    config = _config()
    if not config["enabled"]:
        raise ProdigiAdapterError("prodigi_execution_disabled")
    if not path.startswith("/") or path.startswith("//"):
        raise ProdigiAdapterError("prodigi_path_invalid")
    url = f'{config["base_url"]}{path}'
    parsed = parse.urlparse(url)
    if parsed.scheme != "https" or str(parsed.hostname or "").lower() != config["allowed_host"]:
        raise ProdigiAdapterError("prodigi_destination_rejected")
    return config, url


def _json_request(path: str, *, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    config, url = _url(path)
    body = None
    headers = {
        "X-API-Key": str(config["api_key"]),
        "Accept": "application/json",
        "User-Agent": "OAP-Prodigi-Adapter/1.0",
    }
    if payload is not None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(body) > _MAX_REQUEST_BYTES:
            raise ProdigiAdapterError("prodigi_payload_too_large")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, method=method, headers=headers)
    try:
        with request.build_opener(_NoRedirect).open(req, timeout=_TIMEOUT_SECONDS) as response:
            if not 200 <= int(response.status) < 300:
                raise ProdigiAdapterError("prodigi_request_rejected")
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except error.HTTPError as exc:
        raise ProdigiAdapterError("prodigi_http_error") from exc
    except error.URLError as exc:
        raise ProdigiAdapterError("prodigi_unavailable") from exc
    except TimeoutError as exc:
        raise ProdigiAdapterError("prodigi_timeout") from exc
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise ProdigiAdapterError("prodigi_response_too_large")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProdigiAdapterError("prodigi_response_invalid") from exc
    if not isinstance(value, dict):
        raise ProdigiAdapterError("prodigi_response_invalid")
    return value


def submit_order(*, payload: object, idempotency_key: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ProdigiAdapterError("prodigi_order_payload_required")
    key = str(idempotency_key or "").strip()
    if len(key) < 8 or len(key) > 160:
        raise ProdigiAdapterError("prodigi_idempotency_key_invalid")
    outbound = dict(payload)
    outbound.setdefault("idempotencyKey", key)
    response = _json_request("/v4.0/Orders", method="POST", payload=outbound)
    order = response.get("order")
    if not isinstance(order, dict):
        raise ProdigiAdapterError("prodigi_order_receipt_missing")
    reference = str(order.get("id") or "").strip()
    if not reference.startswith("ord_"):
        raise ProdigiAdapterError("prodigi_order_reference_invalid")
    stage = str((order.get("status") or {}).get("stage") or response.get("outcome") or "CREATED").upper()
    digest = hashlib.sha256(f"pod|prodigi|{key}|{reference}|{stage}".encode()).hexdigest()
    return {
        "kind": "pod",
        "provider_id": "prodigi",
        "provider_reference": reference,
        "provider_state": stage[:40],
        "idempotency_key": key,
        "receipt_hash": digest,
        "provider_execution_performed": True,
        "secret_values_exposed": False,
        "sandbox": bool(_config()["sandbox"]),
        "human_authority_final": True,
    }


def get_order(*, provider_reference: object) -> dict[str, object]:
    reference = str(provider_reference or "").strip()
    if not reference.startswith("ord_") or len(reference) > 80:
        raise ProdigiAdapterError("prodigi_order_reference_invalid")
    response = _json_request(f"/v4.0/Orders/{reference}", method="GET")
    order = response.get("order")
    if not isinstance(order, dict):
        raise ProdigiAdapterError("prodigi_order_readback_missing")
    status_obj = order.get("status") if isinstance(order.get("status"), dict) else {}
    shipments = order.get("shipments") if isinstance(order.get("shipments"), list) else []
    return {
        "provider_id": "prodigi",
        "provider_reference": str(order.get("id") or reference),
        "provider_state": str(status_obj.get("stage") or "").upper()[:40],
        "shipment_count": len(shipments),
        "readback_performed": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def quote(*, payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ProdigiAdapterError("prodigi_quote_payload_required")
    response = _json_request("/v4.0/quotes", method="POST", payload=dict(payload))
    return {
        "provider_id": "prodigi",
        "outcome": str(response.get("outcome") or ""),
        "quotes": response.get("quotes") if isinstance(response.get("quotes"), list) else [],
        "provider_execution_performed": True,
        "order_created": False,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }
