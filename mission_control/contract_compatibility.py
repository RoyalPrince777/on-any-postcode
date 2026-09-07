"""Quiet compatibility for retired private-control addresses and UI contracts.

This module exists only to keep already-rendered Founder controls functional while
canonical private addresses live under ``/mission``. Public OAP remains fail-closed
through ``surface_security``. Compatibility redirects never grant identity,
approval or execution authority.
"""
from __future__ import annotations

from collections.abc import Callable

from flask import Flask, redirect, request

_PRIVATE_REDIRECTS: tuple[tuple[str, str], ...] = (
    ("/smi/brain/evidence-runner/run", "/mission/smi/brain/evidence-runner/run"),
    ("/smi/brain/evidence", "/mission/smi/brain/evidence"),
    ("/smi/deep-dive/simulate", "/mission/smi/deep-dive/simulate"),
    ("/smi/thinking-signals", "/mission/smi/thinking-signals"),
    ("/smi/brain/receipts", "/mission/smi/brain/receipts"),
    ("/war-room/smi-completion", "/mission/war-room/smi-completion"),
    ("/war-room/master-upgrade", "/mission/war-room/master-upgrade"),
    (
        "/war-room/smi-brain/evidence-runner/run",
        "/mission/war-room/smi-brain/evidence-runner/run",
    ),
    ("/war-room/smi-brain/receipts", "/mission/war-room/smi-brain/receipts"),
    ("/war-room/alignment", "/mission/war-room/alignment"),
    ("/war-room/deep-dive", "/mission/war-room/deep-dive"),
    ("/war-room/debug/404", "/mission/war-room/debug/404"),
    ("/alignment/status", "/mission/alignment/status"),
)


def _with_query(target: str) -> str:
    query = request.query_string.decode("ascii", errors="ignore")
    return target + (f"?{query}" if query else "")


def _redirector(target: str) -> Callable[[], object]:
    def handler():
        return redirect(_with_query(target), code=302)

    return handler


def _inject_before_body(page: str, fragment: str) -> str:
    marker = "</body>"
    if marker in page:
        return page.replace(marker, fragment + marker, 1)
    return page + fragment


def register(app: Flask) -> None:
    """Register compatibility routes and visible truth/safety copy."""

    for index, (legacy, canonical) in enumerate(_PRIVATE_REDIRECTS):
        app.add_url_rule(
            legacy,
            endpoint=f"oap_private_compat_{index}",
            view_func=_redirector(canonical),
            methods=["GET"],
        )

    # Two stale url_for endpoint names remain in the legacy Atlas template.
    # They point to redirect-only compatibility addresses, never new products.
    app.add_url_rule(
        "/movement/request-preview-compat",
        endpoint="movement.public_request_preview",
        view_func=_redirector("/movement/request-preview"),
        methods=["GET"],
    )
    app.add_url_rule(
        "/signals-compat",
        endpoint="safe_signals.signals_board",
        view_func=_redirector("/signals"),
        methods=["GET"],
    )

    @app.after_request
    def _restore_locked_public_and_private_copy(response):
        if response.status_code >= 400 or not response.mimetype.startswith("text/html"):
            return response
        path = request.path.rstrip("/") or "/"
        page = response.get_data(as_text=True)

        if path == "/" and 'aria-label="Public OAP World areas"' not in page:
            page = page.replace(
                '<div class="grid">',
                '<div class="grid" aria-label="Public OAP World areas">',
                1,
            )

        if path == "/the-spot/maps-weather-travel" and (
            "Plan routes and stay aware of local conditions." not in page
        ):
            page = _inject_before_body(
                page,
                '<p class="atlas-mini">Plan routes and stay aware of local conditions.</p>',
            )

        if path == "/the-spot/movement-delivery":
            fragment = ""
            if "📶 eSIM" not in page:
                fragment += '<p class="atlas-mini">📶 eSIM · consent-first connectivity</p>'
            if "Carrier activation, dispatch, payment and live tracking stay off" not in page:
                fragment += (
                    '<p class="atlas-warning">Carrier activation, dispatch, payment and '
                    "live tracking stay off</p>"
                )
            if fragment:
                page = _inject_before_body(page, fragment)

        if path == "/mission" and ">Provider Fabric</a>" not in page:
            page = _inject_before_body(
                page,
                '<a href="/mission/providers" class="public-door">Provider Fabric</a>',
            )

        if path == "/mission/war-room" and "OAP Live Signal Legend" not in page:
            page = _inject_before_body(
                page,
                '<section class="mc-panel" aria-label="OAP Live Signal Legend">'
                "<h2>OAP Live Signal Legend</h2>"
                "<p>First-party rule: OAP owns the War Room and its state language.</p>"
                "<p>🟣 Learning · 🟡 Warning · 🔴 Critical · 🟢 Healthy · "
                "proof-verified is shown as 🔵</p>"
                "</section>",
            )

        response.set_data(page)
        return response


def status() -> dict[str, object]:
    return {
        "component": "OAP Private Compatibility Bridge",
        "legacy_private_redirects": len(_PRIVATE_REDIRECTS),
        "canonical_prefix": "/mission",
        "public_authority": False,
        "execution_granted": False,
        "approval_granted": False,
        "human_authority_final": True,
    }
