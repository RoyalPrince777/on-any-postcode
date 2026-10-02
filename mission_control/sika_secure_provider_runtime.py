"""Secure provider-neutral execution runtime for OAP payments and POD.

Secrets are read only from the process environment and are never returned,
persisted in receipts, or included in errors. Provider names and credentials do
not need to appear in source control.

The runtime is fail-closed:
- HTTPS only
- explicit allowed host
- explicit execution enable flag
- bounded payload/response sizes
- idempotency required
- redirects disabled
- credentials never logged/returned
- success requires a provider reference
- webhook verification uses HMAC-SHA256 and constant-time comparison
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request

_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9._:-]{8,160}$")
_PROVIDER_REF = re.compile(r"^[^\x00-\x1f\x7f]{1,240}$")
_MAX_REQUEST_BYTES = 64 * 1024
_MAX_RESPONSE_BYTES = 128 * 1024
_TIMEOUT_SECONDS = 12


class SecureProviderError(RuntimeError):
    """Safe provider-runtime error with no credential material."""


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class ProviderConfig:
    kind: str
    provider_id: str
    base_url: str
    token: str
    webhook_secret: str
    submit_path: str
    refund_path: str
    allowed_host: str
    enabled: bool


def _env(name: str) -> str:
    return str(os.environ.get(name, "") or "").strip()


def _bool_env(name: str) -> bool:
    return _env(name).lower() in {"1", "true", "yes", "on"}


def _config(kind: str) -> ProviderConfig:
    prefix = "OAP_PAYMENT_PROVIDER" if kind == "payment" else "OAP_POD_PROVIDER"
    base_url = _env(f"{prefix}_BASE_URL")
    allowed_host = _env(f"{prefix}_ALLOWED_HOST").lower()
    parsed = parse.urlparse(base_url) if base_url else None
    host = str(parsed.hostname or "").lower() if parsed else ""
    enabled = _bool_env(f"{prefix}_EXECUTION_ENABLED")

    if enabled:
        if not base_url or parsed is None or parsed.scheme != "https":
            raise SecureProviderError(f"{kind}_provider_https_required")
        if not allowed_host or host != allowed_host:
            raise SecureProviderError(f"{kind}_provider_host_not_allowed")

    return ProviderConfig(
        kind=kind,
        provider_id=_env(f"{prefix}_ID"),
        base_url=base_url.rstrip("/"),
        token=_env(f"{prefix}_TOKEN"),
        webhook_secret=_env(f"{prefix}_WEBHOOK_SECRET"),
        submit_path=_env(f"{prefix}_SUBMIT_PATH") or "/v1/submit",
        refund_path=_env(f"{prefix}_REFUND_PATH") or "/v1/refunds",
        allowed_host=allowed_host,
        enabled=enabled,
    )


def configuration_status(kind: str) -> dict[str, object]:
    if kind not in {"payment", "pod"}:
        raise ValueError("unsupported_provider_kind")
    config = _config(kind)
    return {
        "kind": kind,
        "provider_id_present": bool(config.provider_id),
        "base_url_present": bool(config.base_url),
        "token_present": bool(config.token),
        "webhook_secret_present": bool(config.webhook_secret),
        "allowed_host_present": bool(config.allowed_host),
        "execution_enabled": config.enabled,
        "configuration_complete": all(
            (
                config.provider_id,
                config.base_url,
                config.token,
                config.webhook_secret,
                config.allowed_host,
                config.enabled,
            )
        ),
        "secret_values_exposed": False,
        "redirects_allowed": False,
        "idempotency_required": True,
        "https_required": True,
    }


def _safe_url(config: ProviderConfig, path: str) -> str:
    if not config.enabled:
        raise SecureProviderError(f"{config.kind}_provider_execution_disabled")
    if not all(
        (
            config.provider_id,
            config.base_url,
            config.token,
            config.webhook_secret,
            config.allowed_host,
        )
    ):
        raise SecureProviderError(f"{config.kind}_provider_configuration_incomplete")
    if not path.startswith("/") or path.startswith("//"):
        raise SecureProviderError("provider_path_invalid")
    url = f"{config.base_url}{path}"
    parsed = parse.urlparse(url)
    if parsed.scheme != "https" or str(parsed.hostname or "").lower() != config.allowed_host:
        raise SecureProviderError("provider_destination_rejected")
    return url


def _idempotency(value: object) -> str:
    key = str(value or "").strip()
    if not _IDEMPOTENCY.fullmatch(key):
        raise SecureProviderError("provider_idempotency_key_invalid")
    return key


def _body(payload: object) -> bytes:
    if not isinstance(payload, dict):
        raise SecureProviderError("provider_payload_invalid")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    if len(encoded) > _MAX_REQUEST_BYTES:
        raise SecureProviderError("provider_payload_too_large")
    return encoded


def _safe_json_response(raw: bytes) -> dict[str, Any]:
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise SecureProviderError("provider_response_too_large")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecureProviderError("provider_response_invalid") from exc
    if not isinstance(value, dict):
        raise SecureProviderError("provider_response_invalid")
    return value


def _normalized_receipt(
    *,
    kind: str,
    config: ProviderConfig,
    response: dict[str, Any],
    idempotency_key: str,
) -> dict[str, object]:
    reference = str(
        response.get("provider_reference")
        or response.get("id")
        or response.get("reference")
        or ""
    ).strip()
    if not _PROVIDER_REF.fullmatch(reference):
        raise SecureProviderError("provider_reference_missing")
    provider_state = str(
        response.get("status") or response.get("state") or "ACCEPTED"
    ).strip().upper()[:40]
    digest = hashlib.sha256(
        f"{kind}|{config.provider_id}|{idempotency_key}|{reference}|{provider_state}".encode()
    ).hexdigest()
    return {
        "kind": kind,
        "provider_id": config.provider_id,
        "provider_reference": reference,
        "provider_state": provider_state,
        "idempotency_key": idempotency_key,
        "receipt_hash": digest,
        "provider_execution_performed": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def submit(
    *,
    kind: str,
    payload: object,
    idempotency_key: object,
) -> dict[str, object]:
    """Submit an already-authorised request to a configured provider."""

    if kind not in {"payment", "pod"}:
        raise ValueError("unsupported_provider_kind")
    config = _config(kind)
    url = _safe_url(config, config.submit_path)
    key = _idempotency(idempotency_key)
    body = _body(payload)
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Idempotency-Key": key,
            "User-Agent": "OAP-Secure-Provider-Runtime/1.0",
        },
    )
    opener = request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=_TIMEOUT_SECONDS) as response:
            if not 200 <= int(response.status) < 300:
                raise SecureProviderError("provider_submission_rejected")
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except error.HTTPError as exc:
        raise SecureProviderError("provider_submission_http_error") from exc
    except error.URLError as exc:
        raise SecureProviderError("provider_submission_unavailable") from exc
    except TimeoutError as exc:
        raise SecureProviderError("provider_submission_timeout") from exc

    return _normalized_receipt(
        kind=kind,
        config=config,
        response=_safe_json_response(raw),
        idempotency_key=key,
    )


def refund(
    *,
    payload: object,
    idempotency_key: object,
) -> dict[str, object]:
    """Submit an authorised refund/reversal to the payment provider."""

    config = _config("payment")
    url = _safe_url(config, config.refund_path)
    key = _idempotency(idempotency_key)
    body = _body(payload)
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Idempotency-Key": key,
            "User-Agent": "OAP-Secure-Provider-Runtime/1.0",
        },
    )
    opener = request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=_TIMEOUT_SECONDS) as response:
            if not 200 <= int(response.status) < 300:
                raise SecureProviderError("provider_refund_rejected")
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
    except error.HTTPError as exc:
        raise SecureProviderError("provider_refund_http_error") from exc
    except error.URLError as exc:
        raise SecureProviderError("provider_refund_unavailable") from exc
    except TimeoutError as exc:
        raise SecureProviderError("provider_refund_timeout") from exc

    return _normalized_receipt(
        kind="payment_refund",
        config=config,
        response=_safe_json_response(raw),
        idempotency_key=key,
    )


def verify_webhook(
    *,
    kind: str,
    body: bytes,
    timestamp: object,
    signature: object,
    now: int | None = None,
    tolerance_seconds: int = 300,
) -> dict[str, object]:
    """Verify a timestamped HMAC-SHA256 provider callback."""

    if kind not in {"payment", "pod"}:
        raise ValueError("unsupported_provider_kind")
    config = _config(kind)
    if not config.webhook_secret:
        raise SecureProviderError(f"{kind}_webhook_secret_missing")
    if len(body) > _MAX_RESPONSE_BYTES:
        raise SecureProviderError("provider_webhook_too_large")
    try:
        ts = int(str(timestamp))
    except (TypeError, ValueError) as exc:
        raise SecureProviderError("provider_webhook_timestamp_invalid") from exc
    current = int(time.time()) if now is None else int(now)
    if abs(current - ts) > tolerance_seconds:
        raise SecureProviderError("provider_webhook_timestamp_outside_tolerance")
    supplied = str(signature or "").strip().lower().removeprefix("sha256=")
    message = f"{ts}.".encode("ascii") + body
    expected = hmac.new(
        config.webhook_secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    verified = hmac.compare_digest(expected, supplied)
    return {
        "kind": kind,
        "signature_verified": verified,
        "timestamp_verified": True,
        "secret_values_exposed": False,
        "human_authority_final": True,
    }


def status() -> dict[str, object]:
    payment = configuration_status("payment")
    pod = configuration_status("pod")
    return {
        "system": "OAP Secure Provider Runtime",
        "payment_runtime_built": True,
        "pod_runtime_built": True,
        "payment_configuration": payment,
        "pod_configuration": pod,
        "secrets_source": "environment_only",
        "secrets_persisted_by_oap": False,
        "secrets_returned_by_api": False,
        "https_only": True,
        "host_allowlist_required": True,
        "redirects_blocked": True,
        "bounded_network_io": True,
        "idempotency_required": True,
        "signed_webhooks_required": True,
        "refund_runtime_built": True,
        "provider_success_requires_receipt": True,
        "zero_bypass_policy": True,
        "human_authority_final": True,
    }
