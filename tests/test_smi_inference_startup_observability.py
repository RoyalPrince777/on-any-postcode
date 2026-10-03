from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_startup_inference_probe_exposes_memory_durable_and_combined_worker_state():
    code = (ROOT / "gunicorn.conf.py").read_text()
    assert '"worker_recently_seen": bridge.get("worker_recently_seen")' in code
    assert '"durable_worker_fresh": bridge.get("durable_worker_fresh")' in code
    assert '"worker_ready": bridge.get("worker_ready")' in code
    assert '"first_party_inference_ready": inference_probe.get("first_party_inference_ready")' in code


def test_startup_inference_probe_failure_fails_closed_for_all_worker_states():
    code = (ROOT / "gunicorn.conf.py").read_text()
    assert '"worker_recently_seen": False' in code
    assert '"durable_worker_fresh": False' in code
    assert '"worker_ready": False' in code
    assert '"first_party_inference_ready": False' in code
