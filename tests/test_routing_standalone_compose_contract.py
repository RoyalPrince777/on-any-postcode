"""Static fail-closed checks for OAP's portable routing deployment contract."""
from pathlib import Path


def test_standalone_compose_preserves_private_osrm_and_persistent_graph():
    source = Path("routing/compose.yaml").read_text(encoding="utf-8")
    assert "context: .." in source
    assert "dockerfile: routing/Dockerfile" in source
    assert '"127.0.0.1:10000:10000"' in source
    assert "routing-data:/data" in source
    assert "OAP_ROUTING_DATA_DIR: /data" in source
    assert "OAP_ROUTING_PBF_URL:" in source
    assert "restart: unless-stopped" in source
    assert "network_mode: host" not in source
    assert "privileged: true" not in source
    assert "0.0.0.0:10000:10000" not in source
    assert '"10000:10000"' not in source
