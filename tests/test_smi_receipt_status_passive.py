"""Receipt status must never write on GET; proof is explicit and CSRF protected."""
from __future__ import annotations

from flask import Flask

from mission_control import alignment_views


def test_receipt_get_is_passive(monkeypatch):
    app = Flask(__name__)
    writes = []

    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "receipt_backend_status",
        lambda: writes.append("proof") or {"ok": True},
    )
    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "backend_configuration_status",
        lambda: {"durable_backend_configured": True},
    )
    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "latest_receipts",
        lambda limit: {"count": 1, "receipts": []},
    )

    with app.test_request_context("/smi/brain/receipts"):
        response = alignment_views.smi_brain_receipts.__wrapped__()
        payload = response.get_json()
    assert writes == []
    assert payload["status"]["proof_state"] == "not_run_on_read"
    assert payload["status"]["independent_durable_hrm_ready"] is False
    assert payload["status"]["write_read_proof"] is None
    assert response.headers["Cache-Control"] == "no-store"


def test_receipt_post_requires_csrf_and_runs_explicit_proof(monkeypatch):
    app = Flask(__name__)
    writes = []
    monkeypatch.setattr(
        alignment_views.smi_receipt_backend,
        "receipt_backend_status",
        lambda **kwargs: writes.append(kwargs) or {"durable": True, "read_back_ok": True},
    )
    monkeypatch.setattr(alignment_views.web_security, "csrf_valid", lambda request: False)

    with app.test_request_context("/smi/brain/receipts/proof", method="POST"):
        denied = alignment_views.smi_brain_receipts_proof.__wrapped__()
    assert denied.status_code == 403
    assert writes == []

    monkeypatch.setattr(alignment_views.web_security, "csrf_valid", lambda request: True)
    with app.test_request_context("/smi/brain/receipts/proof", method="POST"):
        response = alignment_views.smi_brain_receipts_proof.__wrapped__()
    assert response.status_code == 200
    assert response.get_json()["status"]["read_back_ok"] is True
    assert writes == [{"require_durable": True}]


def test_missing_sqlite_fallback_is_not_created_by_status(monkeypatch, tmp_path):
    from mission_control import smi_receipt_backend

    missing = tmp_path / "receipts.sqlite3"
    for key in (
        "OAP_HRM_DATABASE_URL",
        "OAP_SMI_HRM_DATABASE_URL",
        "OAP_HRM_DATABASE_URL_B64",
        "OAP_SMI_HRM_DATABASE_URL_B64",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OAP_SMI_RECEIPT_DB_PATH", str(missing))

    result = smi_receipt_backend.latest_receipts(5)

    assert result["count"] == 0
    assert result["durable"] is False
    assert not missing.exists()



def test_passive_receipt_host_fingerprint_is_secret_safe(monkeypatch):
    import hashlib

    from mission_control import smi_receipt_backend

    for key in (
        "OAP_HRM_DATABASE_URL",
        "OAP_SMI_HRM_DATABASE_URL",
        "OAP_HRM_DATABASE_URL_B64",
        "OAP_SMI_HRM_DATABASE_URL_B64",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(
        "OAP_HRM_DATABASE_URL",
        "postgresql://private-user:private-password@ep-example.neon.tech/neondb",
    )
    status = smi_receipt_backend.backend_configuration_status()
    assert status["hrm_host_sha256"] == hashlib.sha256(
        b"ep-example.neon.tech"
    ).hexdigest()
    assert status["live_store_identity_proven"] is False
    assert "private-user" not in str(status)
    assert "private-password" not in str(status)
    assert "ep-example.neon.tech" not in str(status)


def test_receipt_host_fingerprint_unconfigured(monkeypatch):
    from mission_control import smi_receipt_backend

    for key in (
        "OAP_HRM_DATABASE_URL",
        "OAP_SMI_HRM_DATABASE_URL",
        "OAP_HRM_DATABASE_URL_B64",
        "OAP_SMI_HRM_DATABASE_URL_B64",
    ):
        monkeypatch.delenv(key, raising=False)
    assert smi_receipt_backend.backend_configuration_status()["hrm_host_sha256"] is None



def test_sqlite_fallback_must_not_pass_durable_hrm_gates(monkeypatch):
    from mission_control import smi_receipt_backend

    monkeypatch.setattr(
        smi_receipt_backend,
        "write_receipt",
        lambda *args, **kwargs: {
            "ok": True,
            "read_back_ok": True,
            "backend": "local_sqlite_receipt_store",
            "durable": False,
            "fallback_used": True,
        },
    )
    result = smi_receipt_backend.receipt_backend_status()
    assert result["write_read_proof"]["ok"] is True
    assert result["hrm_receipt_ready"] is False
    assert result["matrix_learning_receipt_ready"] is False
    assert result["ecosystem_outcome_receipt_ready"] is False
    assert result["independent_durable_hrm_ready"] is False


def test_postgres_requires_actual_readback_for_durable_hrm_gates(monkeypatch):
    from mission_control import smi_receipt_backend

    monkeypatch.setattr(
        smi_receipt_backend,
        "write_receipt",
        lambda *args, **kwargs: {
            "ok": True,
            "read_back_ok": False,
            "backend": "independent_hrm_postgres",
            "durable": True,
            "fallback_used": False,
        },
    )
    assert smi_receipt_backend.receipt_backend_status()["hrm_receipt_ready"] is False

    monkeypatch.setattr(
        smi_receipt_backend,
        "write_receipt",
        lambda *args, **kwargs: {
            "ok": True,
            "read_back_ok": True,
            "backend": "independent_hrm_postgres",
            "durable": True,
            "fallback_used": False,
        },
    )
    assert smi_receipt_backend.receipt_backend_status()["hrm_receipt_ready"] is True

def test_selected_main_writer_fingerprint_is_passive_secret_safe(monkeypatch):
    import hashlib

    from mission_control import smi_receipt_backend

    for key in (
        "OAP_FALLBACK_DATABASE_URL_B64",
        "OAP_PRIMARY_DATABASE_URL_B64",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OAP_DATABASE_AUTHORITY", "fallback")
    monkeypatch.setenv(
        "OAP_PRIMARY_DATABASE_URL",
        "postgresql://primary-user:primary-secret@unused.example/primary",
    )
    monkeypatch.setenv(
        "OAP_FALLBACK_DATABASE_URL",
        "postgresql://writer-user:writer-secret@selected.example/smi",
    )

    status = smi_receipt_backend.backend_configuration_status()
    assert status["main_database_source"] == "fallback_override"
    assert status["main_database_authority"] == "fallback"
    assert status["main_host_sha256"] == hashlib.sha256(
        b"selected.example"
    ).hexdigest()
    assert status["live_store_identity_proven"] is False
    for sensitive in ("writer-user", "writer-secret", "selected.example", "primary-secret", "unused.example"):
        assert sensitive not in str(status)


def test_invalid_writer_configuration_cannot_prove_identity(monkeypatch):
    from mission_control import smi_receipt_backend

    monkeypatch.setenv("OAP_DATABASE_AUTHORITY", "invalid")
    monkeypatch.setenv("OAP_FALLBACK_DATABASE_URL", "postgresql://secret@selected.example/smi")

    status = smi_receipt_backend.backend_configuration_status()
    assert status["main_database_authority"] == "invalid"
    assert status["main_database_source"] == "invalid_authority"
    assert status["main_host_sha256"] is None
    assert status["live_store_identity_proven"] is False



def test_evidence_runner_catalogue_does_not_write_receipts(monkeypatch):
    from mission_control import smi_brain_evidence_runner, smi_receipt_backend

    def unexpected_proof():
        raise AssertionError("catalogue read attempted a durable proof write")

    monkeypatch.setattr(
        smi_receipt_backend, "receipt_backend_status", unexpected_proof
    )
    monkeypatch.setattr(
        smi_receipt_backend,
        "backend_configuration_status",
        lambda: {
            "preferred_backend": "independent_hrm_postgres",
            "durable_backend_configured": True,
        },
    )
    result = smi_brain_evidence_runner.runner_status()
    receipt = result["receipt_backend"]

    assert receipt["proof_state"] == "not_run_on_status_read"
    assert receipt["write_read_proof"] is None
    assert receipt["hrm_receipt_ready"] is False
    assert receipt["matrix_learning_receipt_ready"] is False
    assert receipt["independent_durable_hrm_ready"] is False
    assert result["full_green"] is False


def test_durable_proof_blocks_absent_postgres_without_creating_sqlite(monkeypatch):
    from mission_control import smi_receipt_backend

    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "")
    monkeypatch.setattr(
        smi_receipt_backend,
        "_write_sqlite",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("durable proof must never create SQLite fallback")
        ),
    )
    proof = smi_receipt_backend.receipt_backend_status(require_durable=True)
    assert proof["write_read_proof"]["status"] == "blocked_durable_hrm_unconfigured"
    assert proof["write_read_proof"]["receipt_id"] is None
    assert proof["hrm_receipt_ready"] is False
    assert proof["full_system_green"] is False


def test_durable_proof_preserves_id_when_postgres_commit_state_unknown(monkeypatch):
    from mission_control import smi_receipt_backend

    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "configured")
    monkeypatch.setattr(
        smi_receipt_backend,
        "_write_postgres",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("synthetic uncertain commit or readback")
        ),
    )
    monkeypatch.setattr(
        smi_receipt_backend,
        "_write_sqlite",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("no ephemeral second writer during recovery proof")
        ),
    )
    proof = smi_receipt_backend.receipt_backend_status(require_durable=True)
    result = proof["write_read_proof"]
    assert result["status"] == "durable_commit_or_readback_unconfirmed"
    assert result["receipt_id"].startswith("smi-")
    assert result["ok"] is False
    assert result["read_back_ok"] is False
    assert result["durable"] is False
    assert result["fallback_used"] is False
    assert proof["independent_durable_hrm_ready"] is False


def test_ordinary_receipts_retain_existing_sqlite_fallback(monkeypatch):
    from mission_control import smi_receipt_backend

    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "")
    monkeypatch.setattr(
        smi_receipt_backend,
        "_write_sqlite",
        lambda *args, **kwargs: {"backend": "local_sqlite_receipt_store"},
    )
    receipt = smi_receipt_backend.write_receipt(
        "hrm_neon_evidence_receipt", {"safe_payload": {"probe": False}}
    )
    assert receipt["backend"] == "local_sqlite_receipt_store"


def test_recovery_receipt_commits_before_independent_new_session_readback(monkeypatch):
    import json
    from mission_control import smi_receipt_backend

    events = []
    stored = {}

    class Cursor:
        def __init__(self, role):
            self.role = role

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, values=None):
            events.append((self.role, "sql", sql.split()[0]))
            if sql.lstrip().startswith("INSERT"):
                assert self.role == "writer"
                stored["id"] = values[0]
                stored["kind"] = values[1]
                stored["payload"] = json.loads(values[9])
            if sql == "SET TRANSACTION READ ONLY":
                assert self.role == "reader"
                events.append((self.role, "read_only"))

        def fetchone(self):
            assert self.role == "reader"
            assert ("writer", "committed") in events
            assert ("writer", "closed") in events
            assert ("reader", "read_only") in events
            return {
                "receipt_id": stored["id"],
                "receipt_kind": stored["kind"],
                "payload_json": stored["payload"],
            }

    class Connection:
        def __init__(self, role):
            self.role = role

        def __enter__(self):
            events.append((self.role, "opened"))
            return self

        def __exit__(self, *_args):
            events.append((self.role, "closed"))
            return False

        def cursor(self):
            return Cursor(self.role)

        def commit(self):
            events.append((self.role, "committed"))

    def connect():
        role = "writer" if not events else "reader"
        return Connection(role)

    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "configured")
    monkeypatch.setattr(smi_receipt_backend, "_connect_postgres", connect)
    monkeypatch.setattr(smi_receipt_backend, "_init_postgres_schema", lambda *_args: None)
    monkeypatch.setattr(
        smi_receipt_backend,
        "_write_sqlite",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("recovery proof created nondurable fallback")
        ),
    )

    result = smi_receipt_backend.write_receipt(
        "hrm_neon_evidence_receipt", {"safe_payload": {"probe": True}},
        require_durable=True,
    )
    assert result["ok"] is True
    assert result["read_back_ok"] is True
    assert result["durable"] is True
    assert len(result["read_back_checksum_sha256"]) == 64
    assert result["backend"] == "independent_hrm_postgres"
    assert len([item for item in events if item == ("writer", "committed")]) == 1
    assert ("reader", "read_only") in events
    assert len([item for item in events if item == ("reader", "opened")]) == 1


def test_recovery_second_connection_failure_keeps_uncertain_id_no_second_write(monkeypatch):
    from mission_control import smi_receipt_backend

    calls = []
    original = smi_receipt_backend._write_postgres

    def simulate(*args, **kwargs):
        assert kwargs == {"independent_readback": True}
        calls.append(args[2])
        raise RuntimeError("synthetic failure after first connection committed")

    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "configured")
    monkeypatch.setattr(smi_receipt_backend, "_write_postgres", simulate)
    monkeypatch.setattr(
        smi_receipt_backend,
        "_write_sqlite",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("no duplicate SQLite receipt")
        ),
    )
    result = smi_receipt_backend.write_receipt(
        "hrm_neon_evidence_receipt", {"safe_payload": {"probe": True}},
        require_durable=True,
    )
    assert result["status"] == "durable_commit_or_readback_unconfirmed"
    assert result["receipt_id"] == calls[0]
    assert result["durable"] is False
    assert result["read_back_ok"] is False
    assert len(calls) == 1


def test_independent_recovery_readback_rejects_wrong_stored_payload(monkeypatch):
    from mission_control import smi_receipt_backend

    statements = []
    class Cursor:
        def __init__(self, role):
            self.role = role
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, values=None):
            statements.append((self.role, sql, values))
        def fetchone(self):
            assert self.role == "reader"
            return {
                "receipt_id": next(
                    values[0] for role, sql, values in statements
                    if role == "reader" and sql.startswith("SELECT")
                ),
                "receipt_kind": "hrm_neon_evidence_receipt",
                "payload_json": {"wrong": True},
            }
    class Conn:
        def __init__(self, role):
            self.role = role
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def cursor(self):
            return Cursor(self.role)
        def commit(self):
            statements.append(("writer", "committed", None))
    connection_count = []
    def connect():
        connection_count.append(1)
        return Conn("writer" if len(connection_count) == 1 else "reader")
    monkeypatch.setattr(smi_receipt_backend, "_hrm_database_url", lambda: "configured")
    monkeypatch.setattr(smi_receipt_backend, "_connect_postgres", connect)
    monkeypatch.setattr(smi_receipt_backend, "_init_postgres_schema", lambda *_: None)
    monkeypatch.setattr(
        smi_receipt_backend,
        "_write_sqlite",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("no nondurable fallback during recovery proof")
        ),
    )
    result = smi_receipt_backend.write_receipt(
        "hrm_neon_evidence_receipt", {"safe_payload": {"probe": True}},
        require_durable=True,
    )
    assert len(connection_count) == 2
    assert result["ok"] is False
    assert result["read_back_ok"] is False
    assert result["durable"] is False
    assert result["read_back_checksum_sha256"] is None


def test_recovery_probe_signal_cannot_pre_certify_green(monkeypatch):
    from mission_control import smi_receipt_backend

    captured = {}
    def record(_kind, payload, **kwargs):
        captured.update(payload)
        assert kwargs == {"require_durable": True}
        return {
            "ok": False, "read_back_ok": False, "durable": False,
            "fallback_used": False, "backend": "independent_hrm_postgres",
        }
    monkeypatch.setattr(smi_receipt_backend, "write_receipt", record)
    result = smi_receipt_backend.receipt_backend_status(require_durable=True)
    assert captured["signal"] == "🟣"
    assert result["full_system_green"] is False
