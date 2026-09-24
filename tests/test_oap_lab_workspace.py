"""Bounded LAB notebook storage contract against existing workspace records."""
import json
from collections import defaultdict
from uuid import uuid4

import pytest

from mission_control import oap_lab_workspace as lab
from mission_control import workspaces
from mission_control.oap_lab_research import Notebook


def _notebook(identifier=None, question="First question"):
    return Notebook(
        identifier=identifier or str(uuid4()), mission="debt_dependency",
        domain="artificial_intelligence", question=question,
        hypothesis="A draft", falsification="Evidence against the draft",
    )


@pytest.fixture
def store(monkeypatch):
    rows = defaultdict(list)

    def list_records(owner, workspace, *, title_prefix, limit=100):
        assert workspace == "governance"
        return [
            row for row in reversed(rows[owner])
            if row["title"].startswith(title_prefix)
        ][:limit]

    def add_record(owner, workspace, *, title, body, status):
        assert workspace == "governance"
        assert status == "draft"
        rows[owner].append({"title": title, "body": body, "status": status})
        return str(uuid4())

    monkeypatch.setattr(workspaces, "list_records_with_title_prefix", list_records)
    monkeypatch.setattr(workspaces, "add_record", add_record)
    return rows


def test_save_reopen_and_version_chain(store):
    owner = str(uuid4())
    first = _notebook()
    saved = lab.save(owner, first)
    assert saved["version"] == 1
    assert saved["notebook"]["question"] == "First question"
    assert saved["workspace_record_persisted"] is True
    assert saved["immutable_history_verified"] is False
    assert saved["independent_recovery_verified"] is False
    next_note = _notebook(first.identifier, "Revised question")
    saved2 = lab.save(owner, next_note, expected_last_hash=saved["digest"])
    assert saved2["version"] == 2
    assert lab.reopen(owner, first.identifier)["notebook"]["question"] == "Revised question"
    assert len(store[owner]) == 2


def test_wrong_owner_cannot_reopen_or_update(store):
    owner, other = str(uuid4()), str(uuid4())
    notebook = _notebook()
    result = lab.save(owner, notebook)
    with pytest.raises(lab.NotebookHistoryUnavailable):
        lab.reopen(other, notebook.identifier)
    with pytest.raises(lab.NotebookHistoryUnavailable):
        lab.save(other, notebook, expected_last_hash=result["digest"])
    assert len(store[other]) == 0


def test_stop_stale_and_corrupt_history_fail_closed(store):
    owner = str(uuid4())
    notebook = _notebook()
    with pytest.raises(PermissionError):
        lab.save(owner, notebook, stopped=True)
    saved = lab.save(owner, notebook)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="stale"):
        lab.save(owner, notebook)
    store[owner][0]["body"] = store[owner][0]["body"].replace(
        "First question", "Forged question",
    )
    with pytest.raises(lab.NotebookHistoryUnavailable, match="tampered"):
        lab.reopen(owner, notebook.identifier)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="tampered"):
        lab.save(owner, notebook, expected_last_hash=saved["digest"])


def test_store_failure_and_bounded_history_fail_closed(store, monkeypatch):
    owner = str(uuid4())
    notebook = _notebook()
    monkeypatch.setattr(workspaces, "add_record", lambda *args, **kwargs: (
        (_ for _ in ()).throw(workspaces.WorkspaceUnavailable("failed"))
    ))
    with pytest.raises(workspaces.WorkspaceUnavailable):
        lab.save(owner, notebook)
    assert store[owner] == []


def test_wrong_scope_and_fork_fail_closed(store):
    owner = str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    entry = json.loads(store[owner][0]["body"])
    entry["owner_id"] = str(uuid4())
    store[owner][0]["body"] = json.dumps(entry)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="scope"):
        lab.reopen(owner, notebook.identifier)
    store[owner].clear()
    lab.save(owner, notebook)
    store[owner].append(dict(store[owner][0]))
    with pytest.raises(lab.NotebookHistoryUnavailable, match="forked"):
        lab.reopen(owner, notebook.identifier)


def test_signed_hash_does_not_make_authority_or_title_trustworthy(store):
    owner = str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    original = store[owner][0]["body"]
    store[owner][0]["title"] += "-forged"
    with pytest.raises(lab.NotebookHistoryUnavailable, match="title"):
        lab.reopen(owner, notebook.identifier)
    store[owner][0]["title"] = (
        f"OAP-LAB:{notebook.identifier}:v1"
    )
    entry = json.loads(original)
    entry["publication_authorised"] = True
    payload = {key: value for key, value in entry.items() if key != "digest"}
    entry["digest"] = lab._hash(payload)
    store[owner][0]["body"] = json.dumps(entry)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="review_scope"):
        lab.reopen(owner, notebook.identifier)


def test_notebook_extra_field_cannot_be_restored(store):
    owner = str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    entry = json.loads(store[owner][0]["body"])
    entry["notebook"]["execution_instructions"] = "forbidden"
    payload = {key: value for key, value in entry.items() if key != "digest"}
    entry["digest"] = lab._hash(payload)
    store[owner][0]["body"] = json.dumps(entry)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="review_scope"):
        lab.reopen(owner, notebook.identifier)


def test_archived_or_active_record_rejected_even_if_hash_matches(store):
    owner = str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    store[owner][0]["status"] = "active"
    with pytest.raises(lab.NotebookHistoryUnavailable, match="status"):
        lab.reopen(owner, notebook.identifier)


def test_invalid_recomputed_research_contract_and_version_fail_closed(store):
    owner = str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    entry = json.loads(store[owner][0]["body"])
    entry["notebook"]["mission"] = "not_an_existing_mission"
    payload = {key: value for key, value in entry.items() if key != "digest"}
    entry["digest"] = lab._hash(payload)
    store[owner][0]["body"] = json.dumps(entry)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="history_invalid"):
        lab.reopen(owner, notebook.identifier)
    entry["version"] = True
    store[owner][0]["title"] = f"OAP-LAB:{notebook.identifier}:vTrue"
    payload = {key: value for key, value in entry.items() if key != "digest"}
    entry["digest"] = lab._hash(payload)
    store[owner][0]["body"] = json.dumps(entry)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="version_invalid"):
        lab.reopen(owner, notebook.identifier)


def test_unrelated_workspace_records_do_not_truncate_lab_history(store):
    owner = str(uuid4())
    notebook = _notebook()
    store[owner].extend([
        {"title": f"OTHER:{i}", "body": "unrelated", "status": "draft"}
        for i in range(180)
    ])
    saved = lab.save(owner, notebook)
    assert saved["version"] == 1
    assert lab.reopen(owner, notebook.identifier)["version"] == 1


def test_archived_version_is_not_silently_omitted(store):
    owner = str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    store[owner][0]["status"] = "archived"
    with pytest.raises(lab.NotebookHistoryUnavailable, match="status"):
        lab.reopen(owner, notebook.identifier)
