from __future__ import annotations

from pathlib import Path

from mission_control import maps_movement_direct_proof_runner as runner


def test_dynamic_route_is_skipped_without_network():
    result = runner._probe_status("https://example.test", "/photos/<photo_id>")
    assert result["skipped"] is True
    assert result["status"] is None
    assert result["reason"] == "dynamic_route_requires_concrete_identifier"


def test_route_matrix_capture_is_read_only_and_receipted_in_source():
    source = Path(runner.__file__).read_text(encoding="utf-8")
    section = source.split("def execute_route_matrix_capture", 1)[1].split(
        "def route_matrix_status", 1
    )[0]
    assert '"read_only": True' in section
    assert '"production_state_mutated": False' in section
    assert '"payment_capture": False' in section
    assert '"dispatch": False' in section
    assert '"hidden_tracking": False' in section
    assert "persist_and_read_back" in section
    assert 'action="A6_ROUTE_MATRIX_CAPTURE"' in section


def test_smi_gateway_a6_route_matrix_trigger_is_fail_closed():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert 'OAP_A6_ROUTE_MATRIX_ON_HEALTH' in source
    assert 'OAP_A6_ROUTE_MATRIX_ON_BOOT' in source
    assert 'founder_approved=True' in source
    assert 'guardian_pass=bool(checks.get("guardian_pass"))' in source
    assert 'green_gate_pass=bool(checks.get("green_gate"))' in source
    assert 'rollback_proven=True' in source
    assert 'receipt_chain_ready=bool(checks.get("consequential_action_receipt_chain"))' in source
    assert 'production_state_mutated": False' in source


def test_gateway_authority_resolver_fails_closed_without_unique_authority():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert "def _resolve_a6_human_authority" in source
    assert "single_human_authority_not_proven" in source
    assert "LIMIT 2" in source
    assert "authority.APPROVAL_PERMISSION" in source


def test_gateway_authority_resolver_distinct_order_expression_matches_select():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert "SELECT DISTINCT i.identity_id::text" in source
    assert "ORDER BY i.identity_id::text" in source


def test_gateway_logs_bounded_a6_blocker_reason():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert '"a6_route_matrix_precheck_blocked:"' in source
    assert 'reason = str(exc)[:180] if isinstance(exc, RuntimeError) else ""' in source
    assert '"reason": reason' in source
    assert "readiness=" in source
    assert "matrix=" in source
    assert "matrix_count=" in source
    assert "enabled=" in source


def test_smi_health_records_first_party_observability():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert 'telemetry.record_http_request(path="/healthz", status_code=200' in source


def test_a6_route_matrix_trigger_is_non_blocking_one_shot_for_boot_and_health():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert "_A6_ROUTE_MATRIX_STARTED" in source
    assert '_maybe_start_a6_route_matrix_operation(trigger="boot")' in source
    assert '_maybe_start_a6_route_matrix_operation(trigger="health")' in source
    assert 'name="oap-a6-route-matrix"' in source
    assert "daemon=True" in source
    assert '"event": "oap_a6_route_matrix_capture_started"' in source
    assert '"trigger": trigger' in source
    health = source.split('@app.get("/healthz")', 1)[1].split(
        '@app.route("/<path:path>"', 1
    )[0]
    assert "execute_route_matrix_capture(" not in health
    assert "threading.Thread(" not in health


def test_a6_route_matrix_boot_trigger_is_explicitly_opt_in():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    block = source.split(
        'def _maybe_start_a6_route_matrix_operation', 1
    )[1].split('@app.get("/healthz")', 1)[0]
    assert '"OAP_A6_ROUTE_MATRIX_ON_BOOT"' in block
    assert 'os.environ.get(flag, "").strip() != "1"' in block
    assert "_A6_ROUTE_MATRIX_STARTED.add(operation_id)" in block
    assert "production_state_mutated" in block


def test_route_matrix_uses_real_methods_for_post_only_routes():
    contract = {
        str(item["route"]): item
        for item in runner.ROUTE_MATRIX_CONTRACT
    }
    assert contract["/travel/direct/api/quote"]["method"] == "POST"
    assert 400 in contract["/travel/direct/api/quote"]["expected_statuses"]
    for route in (
        "/mission/supply/suppliers/certify",
        "/mission/supply/listings",
        "/mission/supply/inventory",
        "/mission/supply/reservations/confirm",
        "/movement/route",
        "/movement/bookings",
    ):
        assert contract[route]["method"] == "POST"
        assert 405 not in contract[route]["expected_anonymous_statuses"]


def test_probe_sends_empty_json_for_post_without_mutating_contract(monkeypatch):
    captured = {}

    class Response:
        status = 400

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class Opener:
        def open(self, request, timeout):
            captured["method"] = request.get_method()
            captured["data"] = request.data
            captured["content_type"] = request.headers.get("Content-type")
            return Response()

    monkeypatch.setattr(runner, "build_opener", lambda *args: Opener())
    result = runner._probe_status(
        "https://example.test",
        "/travel/direct/api/quote",
        method="POST",
    )
    assert result["status"] == 400
    assert result["method"] == "POST"
    assert captured == {
        "method": "POST",
        "data": b"{}",
        "content_type": "application/json",
    }


def test_gateway_surfaces_bounded_route_matrix_info_events():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert "_LOGGER.setLevel(logging.INFO)" in source
    assert "_LOGGER.propagate = False" in source
    assert 'logging.StreamHandler()' in source
    assert '"event": "oap_a6_route_matrix_capture"' in source


def test_private_gateway_bootstraps_a6_readiness_before_route_matrix():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert 'OAP_A6_READINESS_ON_BOOT' in source
    assert 'a7_certification.complete_a6_readiness_protocol(' in source
    assert '"execution_granted": False' in source
    assert '"production_state_mutated": False' in source
    readiness_call = source.index("_complete_a6_readiness_if_requested()")
    matrix_call = source.index(
        '_maybe_start_a6_route_matrix_operation(trigger="boot")'
    )
    assert readiness_call < matrix_call


def test_private_gateway_a6_readiness_requires_independent_evidence():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert 'OAP_A6_INDEPENDENT_EVIDENCE_REF' in source
    assert 'OAP_A6_INDEPENDENT_EVIDENCE_HASH' in source
    assert 'OAP_A6_INDEPENDENT_EVIDENCE_ISSUER' in source
    assert 'raise RuntimeError("a6_independent_evidence_not_configured")' in source


def test_gateway_logs_bounded_route_matrix_failures_without_payloads():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert '"failed_public": failed_public' in source
    assert '"failed_private": failed_private' in source
    assert '"route": str(item.get("route") or "")[:120]' in source
    assert '"method": str(item.get("method") or "")[:12]' in source
    assert '"status": item.get("status")' in source
    assert '"network_error": str(item.get("network_error") or "")[:80]' in source
    assert "request.data" not in source


def test_gateway_surfaces_bounded_value_error_reason_for_a6_readiness():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    section = source.split("def _complete_a6_readiness_if_requested", 1)[1].split(
        "def _run_a6_route_matrix_operation", 1
    )[0]
    assert "ValueError" in section
    assert "PermissionError" in section
    assert "str(exc)[:180]" in section


def test_route_matrix_probe_retries_429_only_once(monkeypatch):
    calls = {"open": 0, "sleep": []}

    class Response:
        def __init__(self, status):
            self.status = status

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class Opener:
        def open(self, request, timeout):
            calls["open"] += 1
            if calls["open"] == 1:
                raise runner.HTTPError(request.full_url, 429, "rate", {}, None)
            return Response(200)

    monkeypatch.setattr(runner, "build_opener", lambda *args: Opener())
    monkeypatch.setattr(
        runner.time,
        "sleep",
        lambda seconds: calls["sleep"].append(seconds),
    )

    result = runner._probe_status(
        "https://example.test",
        "/travel",
        method="GET",
    )
    assert result["status"] == 200
    assert calls["open"] == 2
    assert calls["sleep"] == [2.0]


def test_route_matrix_capture_paces_targets(monkeypatch):
    sleeps = []
    monkeypatch.setattr(
        runner.time,
        "sleep",
        lambda seconds: sleeps.append(seconds),
    )
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "if index:" in source
    assert "time.sleep(0.5)" in source
    assert "retry_429=False" in source
    assert '"production_state_mutated": False' in source


def test_private_gateway_health_sequences_observability_before_a6():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    health = source.split('@app.get("/healthz")', 1)[1].split(
        '@app.route("/<path:path>"', 1
    )[0]
    telemetry_call = health.index("telemetry.record_http_request(")
    readiness_call = health.index(
        '_complete_a6_readiness_if_requested(trigger="health")'
    )
    matrix_call = health.index(
        '_maybe_start_a6_route_matrix_operation(trigger="health")'
    )
    assert telemetry_call < readiness_call < matrix_call


def test_private_gateway_lower_green_preparation_is_explicitly_opt_in():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    section = source.split(
        "def _complete_a6_readiness_if_requested", 1
    )[1].split("def _run_a6_route_matrix_operation", 1)[0]
    assert 'OAP_A6_PREPARE_LOWER_GREEN' in section
    assert "smi_proof_gate.prepare_founder_final_evidence(identity_id)" in section
    assert "smi_proof_gate.public_safe_status()" in section
    assert "lower_green_gate_incomplete:" in section
    assert '"execution_granted": False' in section
    assert '"production_state_mutated": False' in section


def test_private_gateway_supports_separate_boot_and_health_readiness_flags():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    section = source.split(
        "def _complete_a6_readiness_if_requested", 1
    )[1].split("def _run_a6_route_matrix_operation", 1)[0]
    assert '"OAP_A6_READINESS_ON_HEALTH"' in section
    assert '"OAP_A6_READINESS_ON_BOOT"' in section
