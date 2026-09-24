"""Bounded LAB notebook storage contract against existing workspace records."""
import json
from collections import defaultdict
from uuid import uuid4

import pytest

from mission_control import oap_lab_workspace as lab, workspaces
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

    def list_records(owner, workspace, *, limit=50):
        assert workspace == "governance"
        return list(reversed(rows[owner]))[:limit]

    def add_record(owner, workspace, *, title, body, status):
        assert workspace == "governance"
        assert status == "draft"
        rows[owner].append({"title": title, "body": body})
        return str(uuid4())

    monkeypatch.setattr(workspaces, "list_records", list_records)
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
    first = lab.save(owner, notebook)
    entry = json.loads(store[owner][0]["body"])
    entry["owner_id"] = str(uuid4())
    store[owner][0]["body"] = json.dumps(entry)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="scope"):
        lab.reopen(owner, notebook.identifier)
    store[owner].clear()
    first = lab.save(owner, notebook)
    store[owner].append(dict(store[owner][0]))
    with pytest.raises(lab.NotebookHistoryUnavailable, match="forked"):
        lab.reopen(owner, notebook.identifier)
