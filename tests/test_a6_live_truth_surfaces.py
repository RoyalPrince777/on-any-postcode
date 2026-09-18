from pathlib import Path


def test_a6_direct_projection_uses_live_matrix_state():
    source = Path("mission_control/maps_movement_direct_proof_views.py").read_text(
        encoding="utf-8"
    )
    assert "a6_matrix_execution.status()" in source
    assert '"A6 Matrix-governed"' in source
    assert '"A7 constitutional locked"' in source
    assert 'state="future_locked"' not in source
    assert 'future_execution_level="A6 future locked"' not in source
