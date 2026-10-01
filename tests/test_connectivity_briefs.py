"""Owner scope, minimisation and audit tests for SMI connectivity briefs."""
import json
from collections import defaultdict
from uuid import uuid4

import pytest

from mission_control import connectivity_briefs as briefs
from mission_control import workspaces


@pytest.fixture
def store(monkeypatch):
    rows = defaultdict(list)
    receipts = defaultdict(list)

    def list_rows(owner, brief_id, *, limit=100):
        return list(reversed(rows[(owner, brief_id)]))[:limit]

    def list_receipts(owner, brief_id, *, limit=100):
        return list(receipts[(owner, brief_id)])[:limit]

    def add(owner, *, brief_id, version, digest, title, body):
        record_id = str(uuid4())
        rows[(owner, brief_id)].append({
            "record_id": record_id, "title": title, "body": body, "status": "draft",
        })
        receipts[(owner, brief_id)].append({
            "event_seq": version, "actor_id": owner,
            "target": f"connectivity_brief:{brief_id}",
            "metadata": {
                "version": version, "digest": digest, "record_id": record_id,
                "prompt_persisted": False, "execution_authorised": False,
                "founder_review_required": True,
            },
        })
        return record_id

    monkeypatch.setattr(workspaces, "list_connectivity_brief_records", list_rows)
    monkeypatch.setattr(workspaces, "list_connectivity_brief_audit_receipts", list_receipts)
    monkeypatch.setattr(workspaces, "add_connectivity_brief_record_atomic", add)
    return rows, receipts


def _brief(brief_id=None, **changes):
    values = {
        "brief_id": brief_id or str(uuid4()),
        "source_run_id": "a" * 32,
        "title": "SMI 6G + ISAC Brief",
        "completed_at": "2026-10-02T08:00:00+01:00",
        "summary": "Measured evidence is bounded and requires Founder review.",
        "evidence_links": ("https://www.itu.int/imt-2030",),
        "evidence_score": 72,
        "decision": "watch",
    }
    values.update(changes)
    return briefs.ConnectivityBrief(**values)


def test_brief_is_minimised_audited_and_idempotent(store):
    owner = str(uuid4())
    brief = _brief()
    saved = briefs.upsert(owner, brief)
    assert saved["changed"] is True
    assert saved["prompt_persisted"] is False
    assert saved["execution_authorised"] is False
    assert saved["founder_approved"] is False
    assert saved["physical_acceptance"] is False
    body = json.loads(store[0][(owner, brief.brief_id)][0]["body"])
    assert "prompt" not in body
    assert "raw_output" not in body
    assert body["brief"]["evidence_links"] == ["https://www.itu.int/imt-2030"]
    again = briefs.upsert(owner, brief, expected_last_hash=saved["digest"])
    assert again["changed"] is False
    assert len(store[0][(owner, brief.brief_id)]) == 1


def test_brief_history_fails_closed_on_wrong_owner_stop_and_tamper(store):
    owner, other = str(uuid4()), str(uuid4())
    brief = _brief()
    briefs.upsert(owner, brief)
    with pytest.raises(briefs.ConnectivityBriefUnavailable, match="not_found"):
        briefs.get(other, brief.brief_id)
    with pytest.raises(PermissionError, match="STOP"):
        briefs.upsert(owner, brief, stopped=True)
    row = store[0][(owner, brief.brief_id)][0]
    row["body"] = row["body"].replace("Founder review", "Automatic approval")
    with pytest.raises(briefs.ConnectivityBriefUnavailable, match="tampered"):
        briefs.get(owner, brief.brief_id)


def test_list_all_returns_only_verified_briefs(store, monkeypatch):
    owner = str(uuid4())
    first, second = _brief(), _brief(title="Second brief")
    briefs.upsert(owner, first)
    briefs.upsert(owner, second)
    monkeypatch.setattr(
        workspaces,
        "list_connectivity_brief_ids",
        lambda identity, *, limit=50: [second.brief_id, first.brief_id],
    )
    values = briefs.list_all(owner)
    assert [item["brief"]["title"] for item in values] == ["Second brief", first.title]
    assert all(item["audit_readback_verified"] is True for item in values)


@pytest.mark.parametrize("changes", [
    {"source_run_id": "short"},
    {"completed_at": "2026-10-02T08:00:00"},
    {"evidence_links": ("http://example.com/paper",)},
    {"evidence_links": ("https://example.com/paper\n",)},
    {"evidence_links": ()},
    {"evidence_score": 101},
    {"decision": "approved"},
    {"source": "untrusted_agent"},
])
def test_invalid_or_authority_expanding_briefs_are_rejected(changes):
    with pytest.raises(ValueError):
        _brief(**changes)


def test_no_material_update_allows_empty_evidence_links():
    brief = _brief(evidence_links=(), no_material_update=True, evidence_score=0)
    assert brief.no_material_update is True
