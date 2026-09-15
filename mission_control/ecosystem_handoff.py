"""Public-safe ecosystem handoff: The Link → Market → Media → Distribution → Store.

This module connects existing OAP discovery/product surfaces without inventing
checkout, external distribution or app-install execution. OAP Store begins as a
first-party catalogue/governance front door; install/update remain proof-gated.
"""
from __future__ import annotations

from html import escape
from typing import Any

from flask import Flask, make_response

CHAIN: tuple[dict[str, str], ...] = (
    {
        "id": "the_link",
        "name": "The Link",
        "route": "/the-link",
        "purpose": "Find people, opportunities and governed paths into OAP products.",
    },
    {
        "id": "market",
        "name": "Market",
        "route": "/the-spot/market",
        "purpose": "Discover products and direct commerce without fake checkout claims.",
    },
    {
        "id": "media",
        "name": "OAP TV & Media",
        "route": "/the-spot/tv-media",
        "purpose": "Move cleared creator media into OAP-owned audience surfaces.",
    },
    {
        "id": "distribution",
        "name": "OAP Distribution",
        "route": "/the-spot/distribution",
        "purpose": "Prepare releases, campaigns and rights proof; external delivery remains gated.",
    },
    {
        "id": "store",
        "name": "OAP Store",
        "route": "/oap-store",
        "purpose": "First-party catalogue for Certified OAP apps, games and tools.",
    },
)

STORE_LOCKS: tuple[str, ...] = (
    "Certified developer identity required before publishing.",
    "Signed package and checksum proof required before install.",
    "Guardian scanning and permission review required before install.",
    "Platform-specific package proof required before native distribution.",
    "Install, update, revoke and rollback execution are not enabled by this surface.",
    "Human Authority remains final for consequential Store governance.",
)


def _index_for_path(path: str) -> int | None:
    normalized = path.rstrip("/") or "/"
    for index, item in enumerate(CHAIN):
        if item["route"] == normalized:
            return index
    return None


def navigation_fragment(path: str) -> str:
    """Return one quiet forward handoff for an existing chain surface."""

    index = _index_for_path(path)
    if index is None:
        return ""
    current = CHAIN[index]
    next_item = CHAIN[index + 1] if index + 1 < len(CHAIN) else None
    chain_text = " → ".join(escape(item["name"]) for item in CHAIN)
    next_html = ""
    if next_item is not None:
        next_html = (
            f'<a class="mc-secondary-link" href="{escape(next_item["route"])}">'
            f'Continue to {escape(next_item["name"])} →</a>'
        )
    return (
        '<section class="mc-panel" data-oap-ecosystem-handoff="true" '
        'aria-label="OAP ecosystem handoff">'
        '<p class="mc-eyebrow">🔗 One connected OAP path</p>'
        f'<h2>{escape(current["name"])} in the OAP ecosystem</h2>'
        f'<p>{chain_text}</p>'
        f'<p>{escape(current["purpose"])}</p>'
        f'<div class="atlas-action-row">{next_html}</div>'
        '</section>'
    )


def store_front_door():
    """Render the truthful first-party Store foundation with execution locked."""

    lock_items = "".join(f"<li>{escape(item)}</li>" for item in STORE_LOCKS)
    response = make_response(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>OAP Store</title></head><body class=\"mc-workspace-body\">"
        '<header class="mc-workspace-header"><div><p class="mc-eyebrow">'
        "OAP World → OAP Store</p><h1>OAP Store</h1>"
        "<p>First-party catalogue for Certified OAP apps, games and tools.</p>"
        "</div></header><main class=\"mc-workspace\">"
        '<section class="mc-panel"><h2>Catalogue foundation</h2>'
        "<p>Discovery and governance are available as the Store foundation. "
        "No package is represented as installable until its signed platform artifact, "
        "checksum, Guardian scan and permissions proof exist.</p>"
        '<div class="mc-status-grid">'
        '<article class="mc-status-card"><strong>Apps</strong><span>Catalogue lane registered.</span></article>'
        '<article class="mc-status-card"><strong>Games</strong><span>Catalogue lane registered.</span></article>'
        '<article class="mc-status-card"><strong>Tools</strong><span>Catalogue lane registered.</span></article>'
        '<article class="mc-status-card"><strong>Certified</strong><span>Certification required before publishing.</span></article>'
        "</div></section>"
        '<section class="mc-panel"><h2>Install remains locked</h2><ul>'
        + lock_items
        + '</ul><p><a href="/">OAP World</a> · <a href="/the-spot/market">Market</a> · '
        '<a href="/the-spot/distribution">Distribution</a></p></section>'
        "</main></body></html>"
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def register(app: Flask) -> None:
    app.add_url_rule(
        "/oap-store",
        endpoint="oap_store_front_door",
        view_func=store_front_door,
        methods=["GET"],
    )


def status() -> dict[str, Any]:
    return {
        "component": "OAP Ecosystem Handoff",
        "chain": tuple(dict(item) for item in CHAIN),
        "chain_length": len(CHAIN),
        "store_front_door_registered": True,
        "catalogue_foundation": True,
        "install_enabled": False,
        "update_enabled": False,
        "package_publish_enabled": False,
        "payment_capture_enabled": False,
        "external_distribution_enabled": False,
        "human_authority_final": True,
    }
