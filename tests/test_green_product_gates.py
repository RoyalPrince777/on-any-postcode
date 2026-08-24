from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import app as app_module
from mission_control import (
    approval_service,
    authority,
    judgement,
    location_intelligence,
    postgres_db,
    smi_chat_runtime,
    workspaces,
)


class Result:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


def test_authority_requires_exact_uuid_or_verified_email(monkeypatch):
    identity = "11111111-1111-4111-8111-111111111111"
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_ID", identity)
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", "authority@example.test")

    assert authority.identity_is_authority(identity) is True
    assert authority.identity_is_authority(
        "22222222-2222-4222-8222-222222222222"
    ) is False
    assert authority.email_is_authority("Authority@Example.Test") is True


def test_judgement_builds_five_explainable_sections_and_keeps_human_sixth():
    review = judgement.assess(
        brain={
            "passed": True,
            "can_execute": False,
            "human_authority_final": True,
            "analysis_summary": "Bounded recommendation.",
            "analysis_confidence": 0.82,
            "guardian_reason": "Safe for review.",
            "high_impact": False,
            "war_room": {"scenarios": ["Proceed", "Delay", "Reject"]},
        },
        response="A governed recommendation for Human Authority review.",
        coherence={"passed": True},
        provider_completed=True,
        provider_id="approved-provider",
    )

    assert review["sections_completed"] == 5
    assert review["total_sections"] == 6
    assert review["human_decision"] is None
    assert review["constitution_consistent"] is True
    assert review["confidence"] == 0.82
    assert len(review["evidence"]) == 3


def test_signed_receipt_detects_tampering(monkeypatch):
    monkeypatch.setenv("OAP_APPROVAL_SIGNING_KEY", "k" * 64)
    now = datetime.now(UTC)
    values = {
        "receipt_id": "11111111-1111-4111-8111-111111111111",
        "request_id": "22222222-2222-4222-8222-222222222222",
        "identity_id": "33333333-3333-4333-8333-333333333333",
        "authority_level": 0,
        "decision": "APPROVED",
        "issued_at": now,
        "expires_at": now + timedelta(hours=1),
        "nonce": "unique-nonce",
        "action_digest": "a" * 64,
    }
    signature = approval_service._signature(**values)
    row = (
        values["receipt_id"],
        values["request_id"],
        values["identity_id"],
        0,
        "APPROVED",
        values["issued_at"],
        values["expires_at"],
        values["action_digest"],
        values["nonce"],
        signature,
    )

    assert approval_service._row_signature_valid(row) is True
    assert approval_service._row_signature_valid((*row[:-1], "0" * 64)) is False


def test_location_hierarchy_uses_real_continents():
    assert location_intelligence._continent("GH") == "Africa"
    assert location_intelligence._continent("GB") == "Europe"
    assert location_intelligence._continent("JP") == "Asia"
    assert location_intelligence._continent("BR") == "South America"
    assert location_intelligence._continent("NZ") == "Oceania"
    assert location_intelligence._continent("unknown") == "World"


def test_my_world_exposes_exactly_twelve_owner_scoped_workspaces():
    assert len(workspaces.WORKSPACES) == 12
    assert len({item["id"] for item in workspaces.WORKSPACES}) == 12
    assert {"governance", "maps", "market", "sika"} <= {
        item["id"] for item in workspaces.WORKSPACES
    }


def test_smi_health_is_exactly_twenty_one_truthful_gates(monkeypatch):
    tables = {
        "smi_messages",
        "smi_conversations",
        "smi_memory_records",
        "smi_judgement_reviews",
        "smi_approval_receipts",
        "oap_guardian_reviews",
        "smi_provider_assignments",
        "oap_identities",
        "oap_role_permissions",
        "audit_events",
    }

    class Connection:
        def execute(self, sql, parameters=None):
            del parameters
            if "information_schema.tables" in sql:
                return Result((name,) for name in tables)
            if "FROM audit_events" in sql:
                return Result()
            if "FROM smi_provider_assignments" in sql:
                return Result(((1,),))
            if "FROM smi_judgement_reviews" in sql:
                return Result(((1,),))
            if "FROM oap_identities" in sql and "JOIN" not in sql:
                return Result(((1,),))
            if "JOIN oap_identity_roles" in sql:
                return Result(((1,),))
            raise AssertionError(sql)

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is True
        yield Connection()

    monkeypatch.setenv("OPENAI_API_KEY", "configured")
    monkeypatch.setattr(
        smi_chat_runtime.live_brain,
        "review",
        lambda **kwargs: {
            "agent_count": 78,
            "brain_region_count": 12,
            "safety_codes": ["SAFE"],
            "passed": True,
            "war_room": {"scenarios": []},
            "can_execute": False,
        },
    )
    monkeypatch.setattr(
        smi_chat_runtime.postgres_db,
        "postgres_status",
        lambda: {"reachable": True, "error": None},
    )
    monkeypatch.setattr(smi_chat_runtime.postgres_db, "connect", connect)
    monkeypatch.setattr(smi_chat_runtime.authority, "status", lambda: {"ready": True})
    monkeypatch.setattr(
        smi_chat_runtime.approval_service, "status", lambda: {"ready": True}
    )

    health = smi_chat_runtime.health()

    assert health["total"] == 21
    assert health["green"] == 21
    assert health["status"] == "green"
    assert health["invariants"] == {
        "execution_locked": True,
        "human_authority_final": True,
    }


def test_platform_health_does_not_depend_on_business_approval(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "db_status",
        lambda: {"reachable": True, "initialized": True},
    )
    monkeypatch.setattr(app_module.neon_auth, "status", lambda: {"valid": True})
    monkeypatch.setattr(app_module, "SESSION_SECRET_CONFIGURED", True)
    monkeypatch.setenv("OAP_AUTH_REQUIRED", "true")

    assert app_module._platform_health_snapshot()["ready"] is True


def test_postgres_migration_sql_is_idempotent_and_versioned():
    sql = postgres_db.render_migration_sql()

    assert "smi_judgement_reviews" in sql
    assert "oap_workspace_records" in sql
    assert "ADD COLUMN IF NOT EXISTS authority_level" in sql
    assert postgres_db.MIGRATION_VERSION in sql
    assert postgres_db.MIGRATION_CHECKSUM in sql
    assert "ON CONFLICT (version) DO NOTHING" in sql
