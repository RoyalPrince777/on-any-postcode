"""First-party OAP Host routing source safety; NOT a running host acceptance."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "deploy" / "oap-routing-selfhost"
COMPOSE = HOST / "compose.yaml"
CADDY = HOST / "Caddyfile"
DOCS = HOST / "README.md"
OSRM_IMAGE = ROOT / "Dockerfile"


def test_existing_osrm_image_is_reused_without_another_route_provider():
    compose = COMPOSE.read_text(encoding="utf-8")
    dockerfile = OSRM_IMAGE.read_text(encoding="utf-8")
    assert "context: ../.." in compose
    assert "dockerfile: Dockerfile" in compose
    assert "image: caddy:2.10.2" in compose
    assert "image: ghcr.io/project-osrm" not in compose
    assert "osrm-routed" in dockerfile
    assert "osrm-extract" in dockerfile
    assert "osrm-partition" in dockerfile
    assert "osrm-customize" in dockerfile
    assert "OAP_ROUTING_PBF_URL" in compose
    assert "https://download.geofabrik.de/" in dockerfile


def test_route_computation_port_is_not_published_to_internet():
    compose = COMPOSE.read_text(encoding="utf-8")
    caddy = CADDY.read_text(encoding="utf-8")
    assert "expose:\n      - \"10000\"" in compose
    assert "10000:10000" not in compose
    assert compose.count("ports:") == 1
    assert '- "80:80"' in compose
    assert '- "443:443"' in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose
    assert "{$OAP_ROUTING_DOMAIN}" in caddy
    assert "method GET" in caddy
    assert "path /route/v1/driving/*" in caddy
    assert "reverse_proxy osrm:10000" in caddy
    assert 'respond "No approved OAP route" 404' in caddy
    assert "file_server" not in caddy


def test_self_host_configuration_and_founder_proof_remain_optional():
    compose = COMPOSE.read_text(encoding="utf-8")
    docs = DOCS.read_text(encoding="utf-8")
    assert "OAP_ROUTING_DOMAIN: ${OAP_ROUTING_DOMAIN:?" in compose
    assert "OAP_OSRM_BASE_URL" in docs
    assert "OAP_OSRM_ALLOWED_HOSTS" in docs
    assert "OAP_ROUTING_OWNED_HOSTS" in docs
    assert "NOT DEPLOYED" in docs
    assert "Founder Final" in docs
    assert "20 real driving routes" in docs
    assert "No services were created" in docs
    for forbidden in ("onrender.com", "router.project-osrm.org"):
        assert forbidden not in compose
        assert forbidden not in caddy
