"""Real PostgreSQL proof for SMI Organiser connectivity-brief persistence."""
from __future__ import annotations

import hashlib
import json
import os
from uuid import uuid4

import pytest

from mission_control import connectivity_briefs, postgres_db

pytestmark = pytest.mark.skipif(
    os.environ.get("OAP_REAL_POSTGRES_PROOF") != "1",
    reason="real PostgreSQL proof is CI-gated",
)


def _brief(brief_id: str, *, title: str) -> connectivity_briefs.ConnectivityBrief:
    return connectivity_briefs.ConnectivityBrief(
        brief_id=brief_id,
        source_run_id="ci-connectivity-brief-20261001",
        title=title,
        completed_at="2026-10-02T08:00:00+01:00",
        summary="Measured evidence remains bounded and requires Founder review.",
        evidence_links=("https://www.itu.int/imt-2030",),
        evidence_score=72,
        decision="watch",
    )


def test_real_postgres_connectivity_brief_write_audit_chain_and_readback(
    monkeypatch,
):
    """Use only CI's ephemeral PostgreSQL; never a production database."""
    database_url = os.environ["OAP_PRIMARY_DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("OAP_LAB_DATABASE_AUTHORITY", "platform_database_url")

    base = postgres_db.init_postgres(assume_yes=True)
    assert base["initialized"] is True
    assert postgres_db.lab_database_source() == "platform_database_url"

    owner = str(uuid4())
    other_owner = str(uuid4())
    brief_id = str(uuid4())
    with postgres_db.connect() as connection:
        connection.execute(
            """INSERT INTO users(id,email,username,display_name,status)
               VALUES (%s,%s,%s,'CI Connectivity Brief Owner','active')""",
            (owner, f"{owner}@example.invalid", f"brief-{owner[:8]}"),
        )
        connection.commit()

    first = connectivity_briefs.upsert(
        owner,
        _brief(brief_id, title="SMI 6G + ISAC Brief"),
    )
    second = connectivity_briefs.upsert(
        owner,
        _brief(brief_id, title="SMI 6G + ISAC Brief — reviewed update"),
        expected_last_hash=first["digest"],
    )

    assert first["changed"] is second["changed"] is True
    assert (first["version"], second["version"]) == (1, 2)
    assert second["audit_readback_verified"] is True
    assert second["prompt_persisted"] is False
    assert second["execution_authorised"] is False
    assert second["founder_approved"] is False
    assert second["physical_acceptance"] is False

    readback = connectivity_briefs.get(owner, brief_id)
    assert readback["digest"] == second["digest"]
    assert readback["brief"]["title"].endswith("reviewed update")
    with pytest.raises(
        connectivity_briefs.ConnectivityBriefUnavailable,
        match="connectivity_brief_not_found",
    ):
        connectivity_briefs.get(other_owner, brief_id)

    with postgres_db.lab_connect(readonly=True) as connection:
        records = connection.execute(
            """SELECT record_id,title,body,status
               FROM oap_workspace_records
               WHERE identity_id=%s
                 AND workspace_id='governance'
                 AND title LIKE %s
               ORDER BY title ASC""",
            (owner, f"OAP-CONNECTIVITY-BRIEF:{brief_id}:v%"),
        ).fetchall()
        receipts = connection.execute(
            """SELECT prev_hash,curr_hash,actor_id,target,metadata
               FROM audit_events
               WHERE actor_id=%s
                 AND action='OAP_CONNECTIVITY_BRIEF_IMPORT'
                 AND target=%s
               ORDER BY event_seq ASC""",
            (owner, f"connectivity_brief:{brief_id}"),
        ).fetchall()

    assert len(records) == len(receipts) == 2
    entries = [json.loads(str(row[2])) for row in records]
    assert [entry["version"] for entry in entries] == [1, 2]
    assert entries[0]["previous_hash"] == "GENESIS"
    assert entries[1]["previous_hash"] == entries[0]["digest"] == first["digest"]
    assert entries[1]["digest"] == second["digest"]
    assert all(row[3] == "draft" for row in records)
    assert all("prompt" not in entry["brief"] for entry in entries)
    assert all("raw_output" not in entry["brief"] for entry in entries)

    for record, receipt in zip(records, receipts, strict=True):
        metadata = receipt[4]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        expected_audit_hash = hashlib.sha256(
            (str(receipt[0]) + canonical).encode("utf-8")
        ).hexdigest()
        assert str(receipt[1]) == expected_audit_hash
        assert str(receipt[2]) == owner
        assert str(receipt[3]) == f"connectivity_brief:{brief_id}"
        assert metadata["record_id"] == str(record[0])
        assert metadata["digest"] == json.loads(str(record[2]))["digest"]
        assert metadata["prompt_persisted"] is False
        assert metadata["execution_authorised"] is False
        assert metadata["founder_review_required"] is True

    assert str(receipts[1][0]) == str(receipts[0][1])
