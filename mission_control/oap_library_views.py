"""Public OAP Library and signed-in learning-book routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template, request

from . import oap_library, oap_library_learning, web_security

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


def _error(code: str, message: str, status_code: int):
    return _library_page(
        make_response(jsonify(error={"code": code, "message": message}), status_code)
    )


def _identity() -> tuple[str, dict[str, object]]:
    user = web_security.current_authenticated_user()
    if user is None:
        raise PermissionError("authentication_required")
    return str(user["id"]), user


def _payload() -> dict[str, object]:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise TypeError("json_object_required")
    return value


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
                chapters=oap_library.FOOD_CHAPTERS,
                checkpoints=oap_library.FOOD_CHECKPOINTS,
                csrf_token=web_security.csrf_token(),
            )
        )
    )


@bp.get("/library/food-book/learning-records")
@web_security.login_required(api=True)
def food_book_learning_records():
    """Return only the signed-in member's private, integrity-checked cards."""

    try:
        identity, _user = _identity()
        records = oap_library_learning.list_records(identity)
        return _library_page(make_response(jsonify(records=records)))
    except (TypeError, ValueError):
        return _error("invalid_request", "The learning-card request is invalid.", 400)
    except oap_library_learning.LibraryLearningUnavailable:
        return _error(
            "private_preserve_unavailable",
            "Private OAP preservation is unavailable. Device download still works.",
            503,
        )


@bp.post("/library/food-book/learning-records")
@web_security.login_required(api=True)
def preserve_food_book_learning_record():
    """Preserve one rights-attested card without making it public."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh and try again.",
            403,
        )
    identity, user = _identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(f"library:{identity}"):
        return _error("rate_limited", "Please wait before saving another card.", 429)
    try:
        payload = _payload()
        record = oap_library_learning.create_record(
            identity,
            food_id=payload.get("food_id"),
            area_id=payload.get("area_id"),
            reflection=payload.get("reflection"),
            rights_attested=payload.get("rights_attested"),
            display_name=user.get("name"),
        )
        return _library_page(make_response(jsonify(record=record), 201))
    except PermissionError as exc:
        if str(exc) == "rights_attestation_required":
            return _error(
                "rights_attestation_required",
                "Confirm that the reflection is yours before preserving it.",
                400,
            )
        return _error("permission_denied", "This learning card cannot be saved.", 403)
    except (TypeError, ValueError) as exc:
        code = str(exc) or "invalid_request"
        return _error(code, "Check the learning card and try again.", 400)
    except oap_library_learning.LibraryLearningUnavailable:
        return _error(
            "private_preserve_unavailable",
            "Private OAP preservation is unavailable. Device download still works.",
            503,
        )


@bp.delete("/library/food-book/learning-records/<record_id>")
@web_security.login_required(api=True)
def delete_food_book_learning_record(record_id: str):
    """Delete only a card owned by the signed-in member."""

    if not web_security.csrf_valid(request):
        return _error(
            "csrf_failed",
            "The secure session expired. Refresh and try again.",
            403,
        )
    identity, _user = _identity()
    if not web_security.PUBLIC_WRITE_LIMITER.allow(f"library:{identity}"):
        return _error("rate_limited", "Please wait and try again.", 429)
    try:
        deleted = oap_library_learning.delete_record(identity, record_id)
    except ValueError:
        return _error("invalid_record", "That learning card is invalid.", 400)
    except oap_library_learning.LibraryLearningUnavailable:
        return _error(
            "private_preserve_unavailable",
            "Private OAP preservation is unavailable.",
            503,
        )
    if not deleted:
        return _error("record_not_found", "That learning card was not found.", 404)
    return _library_page(make_response(jsonify(deleted=True)))
