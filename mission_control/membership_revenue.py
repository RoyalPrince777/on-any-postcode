"""Public OAP membership revenue handoff.

The module intentionally does not process card data, grant Founder authority, or
claim payment success. It only exposes fixed OAP offers and redirects configured
tiers to a Founder-configured HTTPS checkout provider. Provider receipts remain
the payment proof until a separately governed durable verification path exists.
"""
from __future__ import annotations

import ipaddress
import os
from typing import Any
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, make_response, redirect, render_template

bp = Blueprint("membership_revenue", __name__)

MEMBERSHIP_TIERS: tuple[dict[str, Any], ...] = (
    {
        "id": "postcode-founder",
        "name": "Postcode Founder",
        "price_pence": 500,
        "price_display": "£5 / month",
        "checkout_env": "OAP_MEMBERSHIP_POSTCODE_FOUNDER_CHECKOUT_URL",
        "purpose": "Support OAP from the postcode outward.",
    },
    {
        "id": "borough-builder",
        "name": "Borough Builder",
        "price_pence": 1000,
        "price_display": "£10 / month",
        "checkout_env": "OAP_MEMBERSHIP_BOROUGH_BUILDER_CHECKOUT_URL",
        "purpose": "Support borough and district growth.",
    },
    {
        "id": "country-champion",
        "name": "Country Champion",
        "price_pence": 2500,
        "price_display": "£25 / month",
        "checkout_env": "OAP_MEMBERSHIP_COUNTRY_CHAMPION_CHECKOUT_URL",
        "purpose": "Support country-level OAP expansion.",
    },
)


def _tier(tier_id: str) -> dict[str, Any] | None:
    return next((item for item in MEMBERSHIP_TIERS if item["id"] == tier_id), None)


def _safe_checkout_url(raw: str) -> str:
    """Return a configured public HTTPS checkout URL or an empty string.

    The destination comes only from server configuration. Local/private IPs,
    embedded credentials, fragments and non-HTTPS schemes are rejected.
    """
    value = raw.strip()
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    if parsed.scheme.casefold() != "https" or not parsed.hostname:
        return ""
    if parsed.username or parsed.password or parsed.fragment:
        return ""
    host = parsed.hostname.casefold().rstrip(".")
    if host == "localhost" or host.endswith(".local"):
        return ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        return ""
    return value


def checkout_url(tier: dict[str, Any]) -> str:
    return _safe_checkout_url(os.environ.get(str(tier["checkout_env"]), ""))


def public_offer_status() -> dict[str, Any]:
    tiers: list[dict[str, Any]] = []
    for tier in MEMBERSHIP_TIERS:
        ready = bool(checkout_url(tier))
        tiers.append(
            {
                "id": tier["id"],
                "name": tier["name"],
                "price_pence": tier["price_pence"],
                "price_display": tier["price_display"],
                "purpose": tier["purpose"],
                "checkout_ready": ready,
                "checkout_path": f"/membership/checkout/{tier['id']}",
            }
        )
    configured = sum(1 for tier in tiers if tier["checkout_ready"])
    return {
        "status": "ready" if configured else "setup_required",
        "currency": "GBP",
        "billing": "monthly",
        "configured_tiers": configured,
        "total_tiers": len(tiers),
        "tiers": tiers,
        "public_browsing_free": True,
        "payment_processed_by_oap": False,
        "card_data_collected_by_oap": False,
        "founder_authority_granted": False,
        "fulfilment": "provider_receipt_then_manual_confirmation",
    }


@bp.get("/membership")
def membership_page():
    return render_template("membership_revenue.html", offer=public_offer_status())


@bp.get("/membership/status")
def membership_status():
    response = jsonify(public_offer_status())
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/membership/checkout/<tier_id>")
def membership_checkout(tier_id: str):
    tier = _tier(tier_id)
    if tier is None:
        return jsonify({"error": {"code": "membership_tier_not_found"}}), 404
    destination = checkout_url(tier)
    if not destination:
        response = make_response(
            render_template(
                "membership_revenue.html",
                offer=public_offer_status(),
                checkout_error="Payment setup required. This tier is not collecting money yet.",
            ),
            503,
        )
        response.headers["Cache-Control"] = "no-store"
        return response
    response = redirect(destination, code=303)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@bp.get("/membership/payment-return")
def membership_payment_return():
    """Truthful post-checkout landing page; never treats a browser return as proof."""
    response = make_response(
        render_template(
            "membership_payment_return.html",
            state="pending_provider_confirmation",
        )
    )
    response.headers["Cache-Control"] = "no-store"
    return response
