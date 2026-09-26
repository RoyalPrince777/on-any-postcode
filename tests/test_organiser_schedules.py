"""Privacy, owner-scope and fail-closed tests for SMI Organiser schedules."""
import json
from collections import defaultdict
from uuid import uuid4

import pytest

from mission_control import organiser_schedules as schedules
from mission_control import workspaces


@pytest.fixture
def store(monkeypatch):
    rows = defaultdict(list)
    receipts = defaultdict(list)

    def list_rows(owner, external_id, *, limit=100):
        return list(reversed(rows[(owner, external_id)]))[:limit]

    def list_receipts(owner, external_id, *, limit=100):
        return list(receipts[(owner, external_id)])[:limit]

    def add(owner, *, external_id, version, digest, title, body):
        record_id = str(uuid4())
        rows[(owner, external_id)].append({
            "record_id": record_id, "title": title, "body": body, "status": "draft",
        })
        receipts[(owner, external_id)].append({
            "event_seq": version, "actor_id": owner,
            "target": f"smi_organiser_schedule:{external_id}",
            "metadata": {
                "workspace_id": "governance", "external_id": external_id,
                "version": version, "digest": digest, "record_id": record_id,
                "record_status": "draft", "prompt_persisted": False,
                "execution_authorised": False,
            },
        })
        return record_id

    monkeypatch.setattr(workspaces, "list_organiser_schedule_records", list_rows)
    monkeypatch.setattr(workspaces, "list_organiser_schedule_audit_receipts", list_receipts)
    monkeypatch.setattr(workspaces, "add_organiser_schedule_record_atomic", add)
    return rows, receipts


def _schedule(external_id="a" * 32, *, title="OAP Data Research", enabled=True):
    return schedules.OrganiserSchedule(
        external_id=external_id,
        title=title,
        schedule="BEGIN:VEVENT\nRRULE:FREQ=WEEKLY;BYDAY=FR\nEND:VEVENT",
        timing_mode="flexible_schedule",
        timezone="Europe/London",
        enabled=enabled,
    )


def test_schedule_is_minimised_audited_and_idempotent(store):
    owner = str(uuid4())
    saved = schedules.upsert(owner, _schedule())
    assert saved["changed"] is True
    assert saved["prompt_persisted"] is False
    body = json.loads(store[0][(owner, "a" * 32)][0]["body"])
    assert "prompt" not in body
    assert body["schedule"]["title"] == "OAP Data Research"
    again = schedules.upsert(owner, _schedule(), expected_last_hash=saved["digest"])
    assert again["changed"] is False
    assert len(store[0][(owner, "a" * 32)]) == 1


def test_changed_schedule_appends_version_and_requires_fresh_hash(store):
    owner = str(uuid4())
    first = schedules.upsert(owner, _schedule())
    with pytest.raises(schedules.ScheduleMirrorUnavailable, match="stale"):
        schedules.upsert(owner, _schedule(title="Changed"))
    second = schedules.upsert(
        owner, _schedule(title="Changed"), expected_last_hash=first["digest"],
    )
    assert second["version"] == 2
    assert schedules.get(owner, "a" * 32)["schedule"]["title"] == "Changed"


def test_wrong_owner_stop_and_tampering_fail_closed(store):
    owner, other = str(uuid4()), str(uuid4())
    schedules.upsert(owner, _schedule())
    with pytest.raises(schedules.ScheduleMirrorUnavailable, match="not_found"):
        schedules.get(other, "a" * 32)
    with pytest.raises(PermissionError, match="STOP"):
        schedules.upsert(owner, _schedule(), stopped=True)
    row = store[0][(owner, "a" * 32)][0]
    row["body"] = row["body"].replace("OAP Data Research", "Forged")
    with pytest.raises(schedules.ScheduleMirrorUnavailable, match="tampered"):
        schedules.get(owner, "a" * 32)


@pytest.mark.parametrize("field,value", [
    ("source", "third_party"),
    ("timing_mode", "whenever"),
    ("timezone", "UTC"),
    ("schedule", "RRULE:FREQ=DAILY"),
])
def test_invalid_or_third_party_schedule_rejected(field, value):
    values = {
        "external_id": "a" * 32, "title": "Research",
        "schedule": "BEGIN:VEVENT\nRRULE:FREQ=WEEKLY;BYDAY=FR\nEND:VEVENT",
        "timing_mode": "flexible_schedule", "timezone": "Europe/London",
        "enabled": True, "source": "chatgpt_automation",
    }
    values[field] = value
    with pytest.raises(ValueError):
        schedules.OrganiserSchedule(**values)
