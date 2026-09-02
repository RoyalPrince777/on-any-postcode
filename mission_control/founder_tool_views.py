"""Private read-only Founder tool routes for OAP Mind."""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import web_security
from .founder_github import FounderGitHubReadAdapter

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


def _error(exc: Exception, status_code: int = 400):
    return _no_store(
        make_response(
            jsonify(error={"code": "founder_tool_read_failed", "message": str(exc)}),
            status_code,
        )
    )


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
