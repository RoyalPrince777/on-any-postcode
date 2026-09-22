"""Public OAP Library and signed-in learning-book routes."""

from __future__ import annotations

from flask import Blueprint, make_response, render_template, request

from . import oap_library, web_security

bp = Blueprint("oap_library", __name__)

_LIBRARY_CSP = (
    "default-src 'self'; base-uri 'self'; connect-src 'self'; font-src 'self'; "
    "form-action 'self'; frame-ancestors 'none'; img-src 'self' data:; "
    "object-src 'none'; script-src 'self'; style-src 'self'"
)


def _library_page(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = _LIBRARY_CSP
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@bp.get("/library")
def library_home():
    """Render the public, first-party OAP knowledge catalogue."""

    validation = oap_library.validate_catalog()
    if validation["passed"] is not True:
        return _library_page(
            make_response(
                render_template("oap_library_unavailable.html"),
                503,
            )
        )
    query = str(request.args.get("q") or "").strip()[:80]
    return _library_page(
        make_response(
            render_template(
                "oap_library.html",
                collections=oap_library.filter_collections(query),
                journey=oap_library.LIBRARY_JOURNEY,
                query=query,
            )
        )
    )


@bp.get("/library/food-book")
@bp.get("/mission/food-book")
@web_security.login_required()
def food_book():
    """Render the source-scoped Food Book inside the member boundary."""

    validation = oap_library.validate_catalog()
    if validation["passed"] is not True:
        return _library_page(
            make_response(
                render_template("oap_library_unavailable.html"),
                503,
            )
        )
    return _library_page(
        make_response(
            render_template(
                "oap_food_book.html",
                areas=oap_library.FOOD_AREAS,
                foods=oap_library.FOODS,
                sources=oap_library.FOOD_SOURCES,
            )
        )
    )
