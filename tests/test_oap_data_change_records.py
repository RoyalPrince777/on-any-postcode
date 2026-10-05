from mission_control.oap_data_change_records import (
    build_change_record,
    certification_state,
    status,
)


def test_oap_data_change_record_preserves_truth_boundary_and_evidence():
    record = build_change_record(
        oap_data_id="OAP-PR-1114",
        mission="Richer OAP Engine CSS/layout/image semantics",
        system="OAP Engine",
        before="Bounded simple selector/layout support",
        after="Bounded compound/descendant/child selectors and image semantics",
        files_changed=("oap/browser_engine/css.py", "oap/browser_engine/layout.py"),
        routes_functions_affected=("native render path",),
        tests_run=("Android APK", "engine tests"),
        security_checks=("Advanced Security AI review incomplete: quota",),
        runtime_proof=("immutable runtime image observed live",),
        rollback_point="previous immutable image digest",
        claw_test="No full browser parity claim; unsupported features stay explicit",
        green_gate="GREEN",
        merge_commit="6a373ac0f0b4a2172cc9a1399463ccea649739bc",
        deployment_digest="sha256:81449380296f79198c974d035b6406b46e4468a0ff0040ed667b25e8141b444a",
        truth_boundary=("No Flexbox/Grid", "No decoded media"),
    )
    assert record.oap_data_id == "OAP-PR-1114"
    assert record.green_gate == "GREEN"
    assert certification_state(record) == "CERTIFIED"
    assert "No Flexbox/Grid" in record.truth_boundary


def test_green_without_runtime_proof_does_not_certify():
    record = build_change_record(
        oap_data_id="OAP-PR-X",
        mission="Bounded change",
        system="SMI",
        before="old",
        after="new",
        rollback_point="known prior commit",
        claw_test="failure modes reviewed",
        green_gate="GREEN",
        tests_run=("unit",),
        merge_commit="abc123",
    )
    assert certification_state(record) == "UNCERTAIN"


def test_non_green_state_is_preserved():
    record = build_change_record(
        oap_data_id="OAP-PR-Y",
        mission="Bounded change",
        system="SMI",
        before="old",
        after="new",
        rollback_point="known prior commit",
        claw_test="failure modes reviewed",
        green_gate="BLOCKED",
    )
    assert certification_state(record) == "BLOCKED"


def test_status_declares_non_mutating_boundary():
    payload = status()
    assert payload["canonical"] is True
    assert payload["mutates_repository"] is False
    assert payload["approves_changes"] is False
    assert payload["deploys"] is False
