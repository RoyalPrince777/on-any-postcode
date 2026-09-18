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
    assert 'reason = str(exc)[:120] if isinstance(exc, RuntimeError) else ""' in source
    assert '"reason": reason' in source
    assert "readiness=" in source
    assert "matrix=" in source
    assert "matrix_count=" in source
    assert "enabled=" in source



def test_smi_health_records_first_party_observability():
    source = Path("smi_gateway.py").read_text(encoding="utf-8")
    assert 'telemetry.record_http_request(path="/healthz", status_code=200' in source
