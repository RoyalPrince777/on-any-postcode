from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TURN = ROOT / "ops" / "turn"


def test_turn_shell_scripts_have_valid_bash_syntax():
    bash = shutil.which("bash")
    if bash is None:
        return
    for path in (TURN / "start-turn.sh", TURN / "verify-turn-external.sh"):
        subprocess.run(
            [bash, "-n", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )


def test_turn_launcher_uses_rest_secret_and_bounded_relay_range():
    source = (TURN / "start-turn.sh").read_text(encoding="utf-8")

    for required in (
        "use-auth-secret",
        "static-auth-secret=$OAP_TURN_SHARED_SECRET",
        "realm=$OAP_TURN_REALM",
        "external-ip=$OAP_TURN_EXTERNAL_IP",
        "min-port=49152",
        "max-port=49252",
        "no-multicast-peers",
        "no-software-attribute",
        "address.is_global",
        "umask 077",
    ):
        assert required in source

    for denied in (
        "10.0.0.0-10.255.255.255",
        "100.64.0.0-100.127.255.255",
        "127.0.0.0-127.255.255.255",
        "169.254.0.0-169.254.255.255",
        "172.16.0.0-172.31.255.255",
        "192.168.0.0-192.168.255.255",
    ):
        assert f"denied-peer-ip={denied}" in source

    assert "allow-loopback-peers" not in source
    assert "set -x" not in source


def test_turn_example_contains_no_real_secret_or_certification_claim():
    example = (TURN / "oap-turn.env.example").read_text(encoding="utf-8")

    assert "REPLACE_WITH_64_CHAR_BASE64URL_SECRET" in example
    assert "example.invalid" in example
    assert "OAP_LINK_TURN_RELAY_VERIFIED=true" not in example


def test_external_probe_requires_explicit_external_context_and_full_paths():
    source = (TURN / "verify-turn-external.sh").read_text(encoding="utf-8")

    for required in (
        'OAP_TURN_EXTERNAL_PROBE:-}" != "true"',
        "turnutils_uclient",
        'run_probe "UDP" -p 3478',
        'run_probe "TCP" -t -p 3478',
        "-verify_hostname",
        'run_probe "TLS" -t -S -p 5349',
        "OAP_TURN_EXTERNAL_RELAY_PROOF_V1_PASS",
    ):
        assert required in source

    assert "set -x" not in source


def test_turn_systemd_unit_keeps_secret_in_root_managed_environment_file():
    unit = (TURN / "oap-turn.service").read_text(encoding="utf-8")

    assert "EnvironmentFile=/etc/oap-turn/oap-turn.env" in unit
    assert "User=turnserver" in unit
    assert "NoNewPrivileges=true" in unit
    assert "ProtectSystem=strict" in unit
    assert "ProtectHome=true" in unit
    assert "PrivateDevices=true" in unit
