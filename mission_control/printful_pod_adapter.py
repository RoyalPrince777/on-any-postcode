"""Printful POD adapter for OAP Supplier Bridge.

Provider-specific transport only. OAP remains the order owner and authority.
This adapter may create/read draft Printful orders, but it never confirms an
order for fulfillment because confirmation can trigger charging/production.
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
_PRINTFUL_HOST = "api.printful.com"


class PrintfulAdapterError(RuntimeError):
    """Safe adapter error without credential material."""


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _env(name: str) -> str:
    return str(os.environ.get(name, "") or "").strip()


def _enabled() -> bool:
    return _env("OAP_POD_PROVIDER_EXECUTION_ENABLED").lower() in {"1","true","yes","on"}


def _config() -> dict[str, object]:
    provider_id = _env("OAP_POD_PROVIDER_ID").lower()
    base_url = _env("OAP_POD_PROVIDER_BASE_URL").rstrip("/")
    allowed_host = _env("OAP_POD_PROVIDER_ALLOWED_HOST").lower()
    token = _env("OAP_POD_PROVIDER_TOKEN")
    parsed = parse.urlparse(base_url) if base_url else None
    host = str(parsed.hostname or "").lower() if parsed else ""
    if provider_id and provider_id != "printful":
        raise PrintfulAdapterError("printful_provider_id_required")
    if _enabled():
        if not base_url or parsed is None or parsed.scheme != "https":
            raise PrintfulAdapterError("printful_https_required")
        if host != allowed_host or host != _PRINTFUL_HOST:
            raise PrintfulAdapterError("printful_host_not_allowed")
        if not token:
            raise PrintfulAdapterError("printful_token_missing")
    return {
        "provider_id": provider_id,
        "base_url": base_url,
        "allowed_host": allowed_host,
        "token": token,
        "enabled": _enabled(),
        "host": host,
    }


def status() -> dict[str, object]:
    config = _config()
    return {
        "adapter": "printful",
        "provider_id_present": config["provider_id"] == "printful",
        "base_url_present": bool(config["base_url"]),
        "token_present": bool(config["token"]),
        "allowed_host_present": bool(config["allowed_host"]),
        "execution_enabled": bool(config["enabled"]),
        "configuration_complete": all((
            config["provider_id"] == "printful",
            config["base_url"],
            config["token"],
            config["allowed_host"] == _PRINTFUL_HOST,
            config["enabled"],
        )),
        "auth_scheme": "Bearer",
        "draft_order_create_supported": True,
        "order_readback_supported": True,
        "automatic_fulfilment_confirmation": False,
        "charge_triggering_confirmation_blocked": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def _url(path: str) -> tuple[dict[str, object], str]:
    config = _config()
    if not config["enabled"]:
        raise PrintfulAdapterError("printful_execution_disabled")
    if not path.startswith("/") or path.startswith("//"):
        raise PrintfulAdapterError("printful_path_invalid")
    url = f'{config["base_url"]}{path}'
    parsed = parse.urlparse(url)
    if parsed.scheme != "https" or str(parsed.hostname or "").lower() != _PRINTFUL_HOST:
        raise PrintfulAdapterError("printful_destination_rejected")
    return config, url


def _json_request(path: str, *, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    config, url = _url(path)
    body = None
    headers = {
        "Authorization": f'Bearer {config["token"]}',
        "Accept": "application/json",
        "User-Agent": "OAP-Printful-Adapter/1.0",
    }
    if payload is not None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(body) > _MAX_REQUEST_BYTES:
            raise PrintfulAdapterError("printful_payload_too_large")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, method=method, headers=headers)
    try:
        with request.build_opener(_NoRedirect).open(req, timeout=_TIMEOUT_SECONDS) as response:
            if not 200 <= int(response.status) < 300:
                raise PrintfulAdapterError("printful_request_rejected")
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except error.HTTPError as exc:
        raise PrintfulAdapterError("printful_http_error") from exc
    except error.URLError as exc:
        raise PrintfulAdapterError("printful_unavailable") from exc
    except TimeoutError as exc:
        raise PrintfulAdapterError("printful_timeout") from exc
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise PrintfulAdapterError("printful_response_too_large")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrintfulAdapterError("printful_response_invalid") from exc
    if not isinstance(value, dict):
        raise PrintfulAdapterError("printful_response_invalid")
    return value


def create_draft_order(*, payload: object, idempotency_key: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise PrintfulAdapterError("printful_order_payload_required")
    key = str(idempotency_key or "").strip()
    if len(key) < 8 or len(key) > 160:
        raise PrintfulAdapterError("printful_idempotency_key_invalid")
    outbound = dict(payload)
    outbound.setdefault("external_id", f"oap-{key}"[:120])
    response = _json_request("/orders", method="POST", payload=outbound)
    order = response.get("result")
    if not isinstance(order, dict):
        raise PrintfulAdapterError("printful_order_receipt_missing")
    reference = str(order.get("id") or "").strip()
    if not reference or len(reference) > 80:
        raise PrintfulAdapterError("printful_order_reference_invalid")
    state = str(order.get("status") or "draft").upper()[:40]
    digest = hashlib.sha256(f"pod|printful|{key}|{reference}|{state}".encode()).hexdigest()
    return {
        "kind": "pod",
        "provider_id": "printful",
        "provider_reference": reference,
        "provider_state": state,
        "idempotency_key": key,
        "receipt_hash": digest,
        "provider_execution_performed": True,
        "order_created": True,
        "order_confirmed": False,
        "fulfilment_started": False,
        "charge_triggering_confirmation_blocked": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def get_order(*, provider_reference: object) -> dict[str, object]:
    reference = str(provider_reference or "").strip()
    if not reference or len(reference) > 80:
        raise PrintfulAdapterError("printful_order_reference_invalid")
    response = _json_request(f"/orders/{parse.quote(reference, safe='')}", method="GET")
    order = response.get("result")
    if not isinstance(order, dict):
        raise PrintfulAdapterError("printful_order_readback_missing")
    return {
        "provider_id": "printful",
        "provider_reference": str(order.get("id") or reference),
        "provider_state": str(order.get("status") or "").upper()[:40],
        "readback_performed": True,
        "order_confirmed": bool(order.get("status") not in {None, "", "draft", "pending"}),
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def confirm_order(*args, **kwargs):
    del args, kwargs
    raise PrintfulAdapterError("printful_confirmation_requires_explicit_separate_authority")
