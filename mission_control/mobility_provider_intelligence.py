"""Bounded mobility provider intelligence for OAP Map Intelligence.

OAP Direct is first-party. External providers remain optional adapters and never
become OAP authority. Uber estimates are fetched only when explicit approval and
an access token are configured. No nearby-person or driver tracking is stored.
"""
from __future__ import annotations

import json
import os
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

_UBER_HOST = "api.uber.com"
_TIMEOUT_SECONDS = 5
_MAX_BYTES = 512 * 1024


def _uber_enabled() -> bool:
    return (
        str(os.environ.get("OAP_UBER_API_APPROVED") or "").strip() == "1"
        and bool(str(os.environ.get("OAP_UBER_ACCESS_TOKEN") or "").strip())
    )


def status() -> dict[str, object]:
    return {
        "component": "OAP Adapter · Mobility Intelligence",
        "providers": [
            {
                "id": "oap_direct",
                "name": "OAP Direct",
                "ownership": "first_party",
                "live_ready": True,
                "authority": "OAP",
            },
            {
                "id": "uber",
                "name": "Uber",
                "ownership": "external",
                "live_ready": _uber_enabled(),
                "approval_required": True,
                "token_configured": bool(
                    str(os.environ.get("OAP_UBER_ACCESS_TOKEN") or "").strip()
                ),
                "provider_is_authority": False,
            },
        ],
        "individual_people_tracking": False,
        "precise_device_location_stored": False,
        "external_provider_telemetry_owned_by_oap": False,
    }


def _json(path: str, params: dict[str, object]) -> object:
    if not _uber_enabled():
        raise RuntimeError("uber_api_not_approved")
    token = str(os.environ.get("OAP_UBER_ACCESS_TOKEN") or "").strip()
    url = f"https://{_UBER_HOST}{path}?{urlparse.urlencode(params)}"
    req = urlrequest.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "ON-ANY-POSTCODE-Mobility/1.0",
        },
    )
    try:
        with urlrequest.urlopen(req, timeout=_TIMEOUT_SECONDS) as response:
            final = urlparse.urlparse(response.geturl())
            if final.scheme != "https" or final.hostname != _UBER_HOST:
                raise RuntimeError("uber_redirect_rejected")
            body = response.read(_MAX_BYTES + 1)
    except (urlerror.URLError, OSError) as exc:
        raise RuntimeError("uber_api_unavailable") from exc
    if len(body) > _MAX_BYTES:
        raise RuntimeError("uber_response_too_large")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise RuntimeError("uber_invalid_response") from exc


def estimates(
    *,
    start_latitude: float,
    start_longitude: float,
    end_latitude: float | None = None,
    end_longitude: float | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "provider": "Uber",
        "provider_is_authority": False,
        "live_ready": _uber_enabled(),
        "time_estimates": [],
        "price_estimates": [],
    }
    if not _uber_enabled():
        result["state"] = "locked"
        result["reason"] = "approved_uber_api_access_required"
        return result

    time_payload = _json(
        "/v1.2/estimates/time",
        {
            "start_latitude": start_latitude,
            "start_longitude": start_longitude,
        },
    )
    if isinstance(time_payload, dict) and isinstance(time_payload.get("times"), list):
        result["time_estimates"] = [
            {
                "display_name": str(item.get("display_name") or "")[:80],
                "estimate_seconds": item.get("estimate"),
                "product_id": str(item.get("product_id") or "")[:120],
            }
            for item in time_payload["times"][:20]
            if isinstance(item, dict)
        ]

    if end_latitude is not None and end_longitude is not None:
        price_payload = _json(
            "/v1.2/estimates/price",
            {
                "start_latitude": start_latitude,
                "start_longitude": start_longitude,
                "end_latitude": end_latitude,
                "end_longitude": end_longitude,
            },
        )
        if isinstance(price_payload, dict) and isinstance(price_payload.get("prices"), list):
            result["price_estimates"] = [
                {
                    "display_name": str(item.get("display_name") or "")[:80],
                    "estimate": str(item.get("estimate") or "")[:80],
                    "currency_code": str(item.get("currency_code") or "")[:12],
                    "duration_seconds": item.get("duration"),
                    "distance_miles": item.get("distance"),
                    "product_id": str(item.get("product_id") or "")[:120],
                }
                for item in price_payload["prices"][:20]
                if isinstance(item, dict)
            ]
    result["state"] = "live"
    return result
