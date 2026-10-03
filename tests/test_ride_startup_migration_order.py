from pathlib import Path

INIT = Path("mission_control/__init__.py")


def test_ride_auto_apply_establishes_movement_schema_first():
    source = INIT.read_text(encoding="utf-8")
    gate = source.index('if os.environ.get("OAP_RIDE_SCHEMA_AUTO_APPLY"')
    movement = source.index("movement_operations.init_movement_schema(", gate)
    ride = source.index('("0001_oap_ride_runtime", oap_ride_runtime.init_schema)', gate)

    assert gate < movement < ride
    assert 'RuntimeError("movement_schema_required_before_ride")' in source
