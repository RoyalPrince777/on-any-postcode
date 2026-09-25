from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "mission_control/static/smi_command_centre.js"
CHECKPOINT = ROOT / "mission_control/checkpoint_views.py"


def test_maps_controls_offer_evidence_backed_public_percentages() -> None:
    command = COMMAND.read_text(encoding="utf-8")
    assert '["📈 Public %"' in command
    assert 'button.dataset.mapsReview==="public-percent"' in command
    assert 'fetch("/mission/map-intelligence"' in command
    assert '"% proven/guarded"' in command
    assert '"% building"' in command
    assert '"% locked"' in command
    assert '"% attention"' in command
    assert "no missing proof hidden" in command


def test_public_percentages_come_from_existing_map_summary_not_static_scores() -> None:
    command = COMMAND.read_text(encoding="utf-8")
    checkpoint = CHECKPOINT.read_text(encoding="utf-8")
    assert 'const counts=summary.counts||{}' in command
    assert 'const total=Number(summary.total_checks||0)' in command
    assert '"score_percent": round((green / total) * 100) if total else 0' in checkpoint
    assert 'counts = {"certified": 0, "guarded": 0, "building": 0, "attention": 0, "locked": 0}' in checkpoint
