"""Mind boundary: internal routing consumes the filtered canonical signal."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smi_routing_uses_thalamus_filtered_signal():
    source = (ROOT / "oap/smi/smi_core.py").read_text(encoding="utf-8")
    assert "signal = self.input_manager.receive(envelope)" in source
    assert "agi_route = self.agi_core.route(signal.content, signal.task_type)" in source
    assert "command_review = self.command_intelligence.review(\n            signal.content,\n            signal.task_type," in source
    assert "self.agi_core.route(request.content, request.task_type)" not in source
    assert "self.command_intelligence.review(\n            request.content," not in source


def test_smi_mind_never_approves_or_executes():
    source = (ROOT / "oap/smi/smi_core.py").read_text(encoding="utf-8")
    assert '"brain_count": 1' in source
    assert '"independent_execute": False' in source
    assert '"independent_approval": False' in source
    assert '"human_authority_final": True' in source
