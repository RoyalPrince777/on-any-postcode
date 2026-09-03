"""Private Founder tool routes for OAP Mind.

Reads execute directly behind the authenticated private boundary. Writes prepare
exact Human-reviewable ActionPlans. Approved execution is delegated only to the
canonical Living Kernel bridge.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from . import web_security
from .founder_action_approval import record_action_decision
from .founder_github import FounderGitHubReadAdapter
from .founder_github_proposals import (
    propose_branch_create,
    propose_file_write,
    propose_pull_request,
)
from .founder_kernel_execution import execute_approved_action
from .founder_kernel_execution import status as kernel_execution_status

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
        raise TypeError("JSON object payload is required")
    return payload


def _csrf_required():
    if not web_security.csrf_valid(request):
        return _error(PermissionError("CSRF validation failed"), 403)
    return None


@bp.get("/tools/github/status")
@web_security.login_required(api=True)
def github_status():
    return _no_store(make_response(jsonify(FounderGitHubReadAdapter().status())))


@bp.get("/tools/github/kernel-status")
@web_security.login_required(api=True)
def github_kernel_status():
    return _no_store(make_response(jsonify(kernel_execution_status())))


@bp.get("/tools/github/repository")
@web_security.login_required(api=True)
def github_repository():
    try:
        return _result(FounderGitHubReadAdapter().repository_summary())
    except (TypeError, ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.get("/tools/github/file")
@web_security.login_required(api=True)
def github_file():
    try:
        path = request.args.get("path", "")
        ref = request.args.get("ref", "main")
        return _result(FounderGitHubReadAdapter().read_file(path, ref=ref))
    except (TypeError, ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.get("/tools/github/search")
@web_security.login_required(api=True)
def github_search():
    try:
        query = request.args.get("q", "")
        limit = request.args.get("limit", "10")
        return _result(FounderGitHubReadAdapter().search_code(query, limit=int(limit)))
    except (TypeError, ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.get("/tools/github/diff/<int:pull_request_number>")
@web_security.login_required(api=True)
def github_diff(pull_request_number: int):
    try:
        return _result(FounderGitHubReadAdapter().pull_request_diff(pull_request_number))
    except (TypeError, ValueError, PermissionError, LookupError, RuntimeError) as exc:
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
    except (TypeError, ValueError, PermissionError, LookupError, RuntimeError) as exc:
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
    except (TypeError, ValueError, PermissionError, LookupError, RuntimeError) as exc:
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
    except (TypeError, ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.post("/tools/github/approvals")
@web_security.login_required(api=True)
def github_action_approval():
    csrf_error = _csrf_required()
    if csrf_error is not None:
        return csrf_error
    try:
        payload = _json_payload()
        result = record_action_decision(
            request_id=payload.get("request_id"),
            identity_id=web_security.authenticated_identity(),
            decision=payload.get("decision"),
            action_type=payload.get("action_type"),
            action_digest=payload.get("action_digest"),
            ttl_seconds=int(payload.get("ttl_seconds", 900)),
        )
        return _no_store(
            make_response(
                jsonify(
                    approval=result,
                    executed=False,
                    next_gate="Living Kernel",
                    human_authority_final=True,
                )
            )
        )
    except (TypeError, ValueError, PermissionError, LookupError, RuntimeError) as exc:
        return _error(exc)


@bp.post("/tools/github/execute")
@web_security.login_required(api=True)
def github_execute_approved_action():
    csrf_error = _csrf_required()
    if csrf_error is not None:
        return csrf_error
    try:
        payload = _json_payload()
        plan = payload.get("plan")
        if not isinstance(plan, dict):
            raise TypeError("Exact approved plan is required")
        result = execute_approved_action(
            identity_id=web_security.authenticated_identity(),
            receipt_id=str(payload.get("receipt_id") or ""),
            plan_payload=plan,
        )
        return _no_store(make_response(jsonify(result)))
    except PermissionError as exc:
        return _error(exc, 403)
    except (TypeError, ValueError, LookupError, RuntimeError) as exc:
        return _error(exc)
