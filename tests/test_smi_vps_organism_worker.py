"""Guard the existing first-party Organism worker Linux VPS service contract.

This validates deployment configuration only. It does not prove live runtime,
provision a host, grant execution permission or mark any Green Gate passed.
"""
from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

UNIT = Path("ops/organism/oap-organism-worker.service")


def _unit() -> ConfigParser:
    parser = ConfigParser(interpolation=None)
    assert parser.read(UNIT, encoding="utf-8") == [str(UNIT)]
    return parser


def test_organism_vps_worker_is_one_existing_bounded_worker():
    unit = _unit()
    service = unit["Service"]
    assert service["Type"] == "simple"
    assert service["User"] == "oap"
    assert service["Group"] == "oap"
    assert service["WorkingDirectory"] == "/opt/on-any-postcode"
    assert service["ExecStart"] == (
        "/opt/on-any-postcode/.venv/bin/python -m mission_control.organism_worker"
    )
    assert service.get("ExecStartPre") is None
    assert "organism-worker.env" in service["EnvironmentFile"]
    assert "DATABASE_URL" not in UNIT.read_text(encoding="utf-8")
    assert "OAP_SMI_GITHUB_READ_TOKEN=" not in UNIT.read_text(encoding="utf-8")


def test_worker_supervisor_is_restartable_but_not_privileged():
    unit = _unit()
    service = unit["Service"]
    assert service["Restart"] == "always"
    assert service["RestartSec"] == "15s"
    assert service["KillSignal"] == "SIGTERM"
    assert service["NoNewPrivileges"] == "true"
    assert service["ProtectSystem"] == "strict"
    assert service["ProtectHome"] == "true"
    assert service["PrivateTmp"] == "true"
    assert service["UMask"] == "0077"
    assert unit["Unit"]["StartLimitBurst"] == "5"
    assert "enable" not in service["ExecStart"].lower()
    assert "deploy" not in service["ExecStart"].lower()
    assert unit["Install"]["WantedBy"] == "multi-user.target"


def test_worker_job_boundary_stays_nonconsequential():
    from mission_control.organism_runtime import ALLOWED_JOB_TYPES

    assert ALLOWED_JOB_TYPES == frozenset(
        {"RUNTIME_HEARTBEAT", "RUNTIME_HEALTH_PROBE"}
    )
