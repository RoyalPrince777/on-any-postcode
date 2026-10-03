from flask import Flask
import pytest

from mission_control import (
    global_transport_views,
    oap_ride_analytics,
    oap_ride_reconciliation_cases,
)


def _app():
    app=Flask(__name__)
    app.secret_key="ride-ops-test"
    app.register_blueprint(global_transport_views.bp)
    return app


def test_ops_routes_registered():
    rules={rule.rule for rule in _app().url_map.iter_rules()}
    assert "/transport/ride/analytics" in rules
    assert "/transport/ride/reconciliation-cases" in rules


def test_reconciliation_case_migration_dry_run_is_bounded():
    state=oap_ride_reconciliation_cases.init_schema(assume_yes=True,dry_run=True)
    assert state["migration"]=="0008_oap_ride_reconciliation_cases"
    assert state["tables"]==1
    assert len(state["checksum"])==64


def test_reconciliation_case_rejects_matched_result_before_store_access():
    with pytest.raises(ValueError,match="matched_reconciliation_needs_no_exception"):
        oap_ride_reconciliation_cases.create_case(
            booking_id="00000000-0000-0000-0000-000000000001",
            reconciliation_result={"state":"MATCHED"},
            provider_id="provider",
            provider_reference="ref",
            evidence_hash="hash",
        )


def test_analytics_rejects_bad_identity_before_store_access():
    with pytest.raises(ValueError,match="invalid_identity_id"):
        oap_ride_analytics.summary(identity_id="bad")
