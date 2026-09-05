"""Safe SIKA value and OAP My Card projections.

This module deliberately models SIKA as an internal value, trust, badge,
membership and receipt layer. It does not move money, initiate payments, offer
cash-out, create deposits, or claim bank/e-money/crypto authority.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class StatusLight:
    id: str
    label: str
    state: str
    value: str
    detail: str


@dataclass(frozen=True)
class Badge:
    id: str
    emoji: str
    label: str
    audience: str
    meaning: str
    state: str = "ready"


@dataclass(frozen=True)
class RevenueStream:
    id: str
    emoji: str
    label: str
    state: str
    price_hint: str
    summary: str


SIKA_DOCTRINE = (
    "SIKA is OAP internal value, trust, badges, receipts, loyalty, membership "
    "and community contribution. Real-money movement stays with regulated "
    "providers and Human Authority approval."
)

COMPLIANCE_LOCKS: tuple[StatusLight, ...] = (
    StatusLight("cash_out", "Cash-out", "locked", "Locked", "SIKA v1 cannot be cashed out or redeemed as money."),
    StatusLight("bank_account", "Bank account", "partner_needed", "Provider needed", "Bank linking must use regulated payment/Open Banking rails."),
    StatusLight("emoney", "E-money", "locked", "Regulated later", "OAP must not issue stored monetary value without the right authorisation."),
    StatusLight("crypto", "Crypto/stablecoin", "locked", "Not enabled", "SIKA v1 is not a crypto token, stablecoin, or investment product."),
    StatusLight("a4_money", "A4 money movement", "blocked", "Blocked", "A4 may review money health, but cannot move money or approve payouts."),
    StatusLight("human_authority", "Human Authority", "live", "Final", "Consequential money decisions terminate at Founder approval."),
)

BADGES: tuple[Badge, ...] = (
    Badge("founder", "👑", "Founder", "Human Authority", "Founder-only command and final approval identity."),
    Badge("member", "🟢", "Member", "Signed-in OAP users", "Active OAP community identity."),
    Badge("sika", "💎", "SIKA Active", "Members and creators", "Internal value, reward, receipt and loyalty status."),
    Badge("certified", "🛡️", "Certified", "Approved profiles", "OAP-reviewed trust marker; certification replaces generic verification."),
    Badge("creator", "🎤", "Creator", "Artists and media", "Creator profile, media, music, culture and promotion tools."),
    Badge("business", "🛍️", "Business", "Local businesses", "Business listing, offers, market and postcode commerce identity."),
    Badge("supplier", "🏨", "Supplier", "Booking/travel supply", "OAP Direct supplier, listing and reservation readiness identity."),
    Badge("youth_safe", "🧒", "Youth Safe", "Protected youth contexts", "Extra protected youth-safe identity and content boundary."),
    Badge("ambassador", "🌍", "Ambassador", "Community leaders", "Postcode, borough, country or global community role."),
)

REVENUE_STREAMS: tuple[RevenueStream, ...] = (
    RevenueStream("memberships", "👑", "Memberships", "ready", "£5 / £10 / £25 launch tiers", "Postcode Founder, Borough Builder and Country Champion tiers."),
    RevenueStream("creator_profiles", "🎤", "Creator Profiles", "ready", "Upgrade tools", "Media pages, music/video showcase, event promotion and creator badges."),
    RevenueStream("business_listings", "🛍️", "Business Listings", "ready", "Free / Featured / Premium", "Postcode spotlight, offers, enquiries, reviews and certified badges."),
    RevenueStream("market", "🧺", "OAP Market", "ready", "Seller plans later", "Creator merch, local products, features and local-commerce tools."),
    RevenueStream("experiences", "🎟️", "OAP Experiences", "ready", "Event fees later", "Watch parties, creator nights, youth-safe activity and vendor slots."),
    RevenueStream("booking", "🏨", "OAP Direct Booking", "needs_finish_pack", "Supplier/booking fees later", "Quote, hold, reservation, confirmation, receipts and cancellation need final proving."),
    RevenueStream("safe_insights", "📊", "Privacy-safe Insights", "later", "Aggregated reports only", "No personal-data sale; only safe aggregated postcode and event insights later."),
)

VALUE_ACTIONS = {
    "earn": [
        "Helpful community contribution",
        "Certified review or correction",
        "Event attendance",
        "Creator or business support",
        "Youth achievement",
        "Safe Signals contribution",
        "Mentorship participation",
    ],
    "redeem": [
        "Membership perks",
        "Profile upgrades",
        "Event discounts",
        "Creator unlocks",
        "Market coupons",
        "Booking credits",
        "Community recognition",
    ],
}


def _asdict_many(items: Iterable[object]) -> list[dict[str, object]]:
    return [asdict(item) for item in items]


def status() -> dict[str, object]:
    return {
        "component": "SIKA Value + My Card",
        "ready": True,
        "sika_doctrine": SIKA_DOCTRINE,
        "financial_authority": "locked",
        "real_money_movement": False,
        "cash_out_allowed": False,
        "bank_provider_required": True,
        "human_authority_final": True,
        "a4_money_movement_allowed": False,
        "status_lights": _asdict_many(COMPLIANCE_LOCKS),
        "badges": _asdict_many(BADGES),
        "revenue_streams": _asdict_many(REVENUE_STREAMS),
        "value_actions": VALUE_ACTIONS,
    }


def my_card(display_name: str = "OAP Member", handle: str = "@oap", *, founder: bool = False) -> dict[str, object]:
    selected_badges = ["member", "sika"]
    if founder:
        selected_badges = ["founder", "sika", "certified", "ambassador"]
    badges = [asdict(badge) for badge in BADGES if badge.id in selected_badges]
    return {
        "component": "My Card",
        "subtitle": "OAP identity card for My World",
        "display_name": display_name or "OAP Member",
        "handle": handle or "@oap",
        "circle": "Postcode to Universe Circle",
        "sika_status": "Active internal value layer",
        "membership_tier": "Founder" if founder else "Member",
        "certification": "Founder Final" if founder else "OAP Member",
        "privacy_note": "This is not government ID, bank ID, payment card, passport or driving licence.",
        "tagline": "Born Local. Built Global.",
        "badges": badges,
        "share_ready": True,
        "qr_ready": False,
    }
