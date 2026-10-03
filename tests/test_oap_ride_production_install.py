from pathlib import Path


def test_ride_schema_auto_apply_is_explicit_and_ordered():
    source = Path("mission_control/__init__.py").read_text(encoding="utf-8")

    assert 'OAP_RIDE_SCHEMA_AUTO_APPLY' in source
    expected = [
        "0001_oap_ride_runtime",
        "0002_oap_ride_guardian",
        "0003_oap_ride_commercial_accessibility",
        "0004_oap_ride_payment_bridge",
        "0005_oap_ride_driver_accessibility",
        "0006_oap_ride_private_geometry",
        "0007_oap_ride_guardian_outbox",
        "0008_oap_ride_reconciliation_cases",
    ]
    positions = [source.index(version) for version in expected]
    assert positions == sorted(positions)
    assert 'assume_yes=True, dry_run=False' in source
    assert '"event": "oap_ride_schema_migration"' in source
    assert '"human_authority_final": True' in source
