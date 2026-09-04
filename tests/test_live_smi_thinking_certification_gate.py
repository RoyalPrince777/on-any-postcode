from __future__ import annotations

import json
from urllib import error as urlerror
from urllib import request as urlrequest

PRIVATE = "https://oap-smi.onrender.com"
PUBLIC = "https://on-any-postcode.onrender.com"
EXPECTED_REVISION = "8cda4a51d248"


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
        return None


def _fetch(url: str) -> tuple[int, dict[str, str], str]:
    opener = urlrequest.build_opener(_NoRedirect())
    request = urlrequest.Request(url, headers={"User-Agent": "OAP-live-certification/1.0"})
    try:
        response = opener.open(request, timeout=30)
    except urlerror.HTTPError as exc:
        response = exc
    try:
        status = int(getattr(response, "status", getattr(response, "code", 0)))
        headers = {key.casefold(): value for key, value in response.headers.items()}
        body = response.read(20000).decode("utf-8", "replace")
        return status, headers, body
    finally:
        response.close()


def test_live_private_smi_certification_and_fail_closed_boundaries():
    status, _, body = _fetch(f"{PRIVATE}/api/smi/thinking-certification")
    assert status == 200
    payload = json.loads(body)
    assert payload["status"] == "certified"
    assert payload["signal"] == "🟢"
    assert payload["gateway_authorized"] is True
    assert payload["founder_auth_bypassed"] is False
    assert payload["revision"] == EXPECTED_REVISION
    certification = payload["certification"]
    assert certification["passed"] == certification["total"]
    assert certification["stage_count"] == 7
    assert certification["stages"] == [
        "understand",
        "context",
        "route",
        "evidence",
        "challenge",
        "synthesise",
        "govern",
    ]
    assert certification["provider_called"] is False
    assert certification["hrm_written"] is False
    assert certification["founder_session_created"] is False
    assert certification["private_reasoning_exposed"] is False
    assert certification["decision_authority"] is False
    assert certification["execution_authority"] is False
    assert certification["human_authority_final"] is True

    public_status, _, _ = _fetch(f"{PUBLIC}/api/smi/thinking-certification")
    assert public_status == 404

    root_status, root_headers, _ = _fetch(f"{PRIVATE}/")
    assert root_status == 302
    assert root_headers.get("location") == "/auth"

    auth_status, _, _ = _fetch(f"{PRIVATE}/auth")
    assert auth_status == 200
