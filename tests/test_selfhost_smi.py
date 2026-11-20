from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SELFHOST = ROOT / "deploy" / "selfhost"


def overlay():
    return yaml.safe_load((SELFHOST / "compose.smi.yaml").read_text())


def test_only_existing_edge_publishes_host_ports():
    for name, service in overlay()["services"].items():
        assert "ports" not in service, name
    assert overlay()["services"]["smi"]["expose"] == ["5000"]
    assert overlay()["services"]["ollama"]["expose"] == ["11434"]


def test_local_dispatch_and_local_inference_do_not_reuse_render_or_external_ai():
    env = overlay()["services"]["smi"]["environment"]
    assert env["OAP_RUNTIME_TARGET"] == "smi_gateway:app"
    assert env["OAP_SMI_LOCAL_DISPATCH"] == "true"
    assert env["OAP_AUTH_REQUIRED"] == "true"
    assert env["OAP_INFERENCE_LOCAL_URL"] == "http://ollama:11434/api/chat"
    assert env["OAP_INFERENCE_COMPATIBILITY_FALLBACK"] == "0"
    assert env["OAP_HOME_NODE_BRIDGE_ENABLED"] == "0"
    assert "onrender.com" not in (SELFHOST / "compose.smi.yaml").read_text()


def test_worker_uses_existing_handlers_and_does_not_receive_write_credentials():
    worker = overlay()["services"]["organism-worker"]
    assert worker["command"] == ["python", "-m", "mission_control.organism_worker"]
    assert worker["env_file"] == ["./.env.worker"]
    assert "OAP_GITHUB_TOKEN" not in worker["environment"]
    assert "OAP_APPROVAL_SIGNING_KEY" not in worker["environment"]
    assert worker["init"] is True
    assert worker["stop_grace_period"] == "45s"


def test_health_hooks_never_self_approve_or_restore_authority():
    env = overlay()["services"]["smi"]["environment"]
    for key in ("OAP_FOUNDER_FINAL_100_ON_HEALTH", "OAP_A6_READINESS_ON_BOOT", "OAP_A6_READINESS_ON_HEALTH", "OAP_A6_ROUTE_MATRIX_ON_BOOT", "OAP_A6_ROUTE_MATRIX_ON_HEALTH"):
        assert env[key] == "0"
    assert env["OAP_RESTORE_CONFIGURED_AUTHORITY_ON_START"] == "false"


def test_private_edge_routes_to_private_service_and_strips_spoofable_headers():
    caddy = (SELFHOST / "Caddyfile.smi").read_text()
    assert "{$OAP_SMI_DOMAIN}" in caddy
    assert "reverse_proxy smi:5000" in caddy
    assert caddy.count("header_up -X-OAP-SMI-Gateway") == 2
    assert caddy.count("header_up -X-OAP-Client-IP") == 2
    assert ".env.*" in (SELFHOST / ".gitignore").read_text()


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite(
        unittest.FunctionTestCase(value)
        for name, value in sorted(globals().copy().items())
        if name.startswith("test_") and callable(value)
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
