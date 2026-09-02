"""Private Founder tool routes for OAP Mind.

Reads execute directly behind the authenticated private boundary. Writes only
prepare exact Human-reviewable ActionPlans; they do not execute here.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import web_security
from .founder_github import FounderGitHubReadAdapter
from .founder_github_proposals import (
    propose_branch_create,
    propose_file_write,
    propose_pull_request,
)

bp = Blueprint("founder_tools", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _result(value):
    return _no_store(
        make_response(
            jsonify(
                operation=value.operation,
                repository=value.repository,
                data=value.data,
                read_only=True,
                human_authority_final=True,
            )
        )
    )


def _proposal(value):
    return _no_store(
        make_response(
            jsonify(
                proposal=value,
                executed=False,
                requires_human_approval=True,
                human_authority_final=True,
            )
        )
    )


def _error(exc: Exception, status_code: int = 400):
    return _no_store(
        make_response(
            jsonify(error={"code": "founder_tool_failed", "message": str(exc)}),
            status_code,
        )
    )


def _json_payload() -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError("JSON object payload is required")
    return payload


def _csrf_required():
    if not web_security.csrf_valid(request):
        return _error(PermissionError("CSRF validation failed"), 403)
    return None


@bp.get("/tools/github/status")
@web_security.login_required(api=True)
def github_status():
    return _no_store(make_response(jsonify(FounderGitHubReadAdapter().status())))


@bp.get("/tools/github/repository")
@web_security.login_required(api=True)
def github_repository():
    try:
        return _result(FounderGitHubReadAdapter().repository_summary())
    except (ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.get("/tools/github/file")
@web_security.login_required(api=True)
def github_file():
    try:
        path = request.args.get("path", "")
        ref = request.args.get("ref", "main")
        return _result(FounderGitHubReadAdapter().read_file(path, ref=ref))
    except (ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.get("/tools/github/search")
@web_security.login_required(api=True)
def github_search():
    try:
        query = request.args.get("q", "")
        limit = request.args.get("limit", "10")
        return _result(FounderGitHubReadAdapter().search_code(query, limit=int(limit)))
    except (ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.get("/tools/github/diff/<int:pull_request_number>")
@web_security.login_required(api=True)
def github_diff(pull_request_number: int):
    try:
        return _result(FounderGitHubReadAdapter().pull_request_diff(pull_request_number))
    except (ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.post("/tools/github/proposals/branch")
@web_security.login_required(api=True)
def github_propose_branch():
    csrf_error = _csrf_required()
    if csrf_error is not None:
        return csrf_error
    try:
        payload = _json_payload()
        return _proposal(
            propose_branch_create(
                branch=payload.get("branch", ""),
                base_sha=payload.get("base_sha", ""),
                request_id=payload.get("request_id"),
            )
        )
    except (ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.post("/tools/github/proposals/file")
@web_security.login_required(api=True)
def github_propose_file_write():
    csrf_error = _csrf_required()
    if csrf_error is not None:
        return csrf_error
    try:
        payload = _json_payload()
        return _proposal(
            propose_file_write(
                branch=payload.get("branch", ""),
                path=payload.get("path", ""),
                content=payload.get("content", ""),
                message=payload.get("message", ""),
                sha=payload.get("sha"),
                request_id=payload.get("request_id"),
            )
        )
    except (ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.post("/tools/github/proposals/pull-request")
@web_security.login_required(api=True)
def github_propose_pull_request():
    csrf_error = _csrf_required()
    if csrf_error is not None:
        return csrf_error
    try:
        payload = _json_payload()
        return _proposal(
            propose_pull_request(
                head=payload.get("head", ""),
                title=payload.get("title", ""),
                body=payload.get("body", ""),
                base=payload.get("base", "main"),
                request_id=payload.get("request_id"),
            )
        )
    except (ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)
