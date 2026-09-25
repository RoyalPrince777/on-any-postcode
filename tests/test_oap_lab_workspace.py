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
    class Store(defaultdict):
        pass

    rows = Store(list)
    receipts = defaultdict(list)

    def list_records(owner, workspace, *, title_prefix, limit=100):
        assert workspace == "governance"
        return [
            row for row in reversed(rows[owner])
            if row["title"].startswith(title_prefix)
        ][:limit]

    def list_receipts(owner, notebook_id, *, limit=100):
        return list(receipts[(owner, notebook_id)])[:limit]

    def add_record(owner, *, title, body, notebook_id, version, digest):
        assert title == f"OAP-LAB:{notebook_id}:v{version}"
        assert len(digest) == 64
        record_id = str(uuid4())
        rows[owner].append({
            "record_id": record_id, "title": title,
            "body": body, "status": "draft",
        })
        receipts[(owner, notebook_id)].append({
            "event_seq": version,
            "actor_id": owner,
            "target": f"oap_lab_notebook:{notebook_id}",
            "metadata": {
                "workspace_id": "governance",
                "notebook_id": notebook_id,
                "version": version,
                "digest": digest,
                "record_id": record_id,
                "record_status": "draft",
                "publication_authorised": False,
                "execution_authorised": False,
            },
        })
        return record_id

    anchors = defaultdict(list)

    def write_anchor(payload):
        receipt_id = str(uuid4())
        anchors[(payload["owner_id"], payload["notebook_id"])].append({
            "receipt_id": receipt_id,
            "payload": dict(payload),
            "backend": "independent_hrm_postgres",
        })
        return {
            "ok": True,
            "status": "written_and_read_back",
            "receipt_id": receipt_id,
            "read_back_ok": True,
            "durable": True,
            "fallback_used": False,
            "backend": "independent_hrm_postgres",
        }

    def read_anchor(*, owner_id, notebook_id, version=None):
        values = anchors[(owner_id, notebook_id)]
        if version is not None:
            values = [
                item for item in values
                if item["payload"].get("version") == version
            ]
        if not values:
            return {
                "ok": False,
                "status": "independent_recovery_anchor_not_found",
                "payload": None,
                "receipt_id": None,
            }
        item = values[-1]
        return {
            "ok": True,
            "status": "independent_recovery_anchor_read",
            "payload": dict(item["payload"]),
            "receipt_id": item["receipt_id"],
            "backend": item["backend"],
            "fallback_used": False,
        }

    monkeypatch.setattr(workspaces, "list_records_with_title_prefix", list_records)
    monkeypatch.setattr(workspaces, "list_lab_audit_receipts", list_receipts)
    monkeypatch.setattr(workspaces, "add_lab_record_atomic", add_record)
    monkeypatch.setattr(lab.smi_receipt_backend, "write_lab_recovery_anchor", write_anchor)
    monkeypatch.setattr(lab.smi_receipt_backend, "read_lab_recovery_anchor", read_anchor)
    rows._lab_receipts = receipts
    rows._lab_anchors = anchors
    return rows


def test_save_reopen_and_version_chain(store):
    owner = str(uuid4())
    first = _notebook()
    saved = lab.save(owner, first)
    assert saved["version"] == 1
    assert saved["notebook"]["question"] == "First question"
    assert saved["workspace_record_persisted"] is True
    assert saved["atomic_audit_write_contract"] is True
    assert saved["audit_readback_verified"] is True
    assert saved["immutable_history_verified"] is False
    assert saved["independent_recovery_verified"] is True
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
    monkeypatch.setattr(workspaces, "add_lab_record_atomic", lambda *args, **kwargs: (
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
    store._lab_receipts[(owner, notebook.identifier)].clear()
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
    with pytest.raises(lab.NotebookHistoryUnavailable, match="receipt_mismatch"):
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
    with pytest.raises(lab.NotebookHistoryUnavailable, match="receipt_mismatch"):
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
    with pytest.raises(lab.NotebookHistoryUnavailable, match="receipt_mismatch"):
        lab.reopen(owner, notebook.identifier)
    entry["version"] = True
    store[owner][0]["title"] = f"OAP-LAB:{notebook.identifier}:vTrue"
    payload = {key: value for key, value in entry.items() if key != "digest"}
    entry["digest"] = lab._hash(payload)
    store[owner][0]["body"] = json.dumps(entry)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="receipt_mismatch"):
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


def test_atomic_audit_failure_cannot_leave_notebook_row(monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.calls = []
            self.committed = False

        def execute(self, sql, params=None):
            self.calls.append((sql, params))
            if "SELECT COUNT(*)" in sql:
                return self
            if "INSERT INTO oap_workspace_records" in sql:
                return self
            if "SELECT curr_hash" in sql:
                return self
            if "INSERT INTO audit_events" in sql:
                raise RuntimeError("audit unavailable")
            return self

        def fetchone(self):
            sql = self.calls[-1][0]
            if "SELECT COUNT(*)" in sql:
                return (0,)
            if "INSERT INTO oap_workspace_records" in sql:
                return (uuid4(),)
            if "SELECT curr_hash" in sql:
                return None
            return None

        def commit(self):
            self.committed = True

    connection = FakeConnection()

    class Context:
        def __enter__(self):
            return connection

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(workspaces.postgres_db, "connect", lambda: Context())
    with pytest.raises(workspaces.WorkspaceUnavailable, match="atomic_audit"):
        workspaces.add_lab_record_atomic(
            str(uuid4()), title=f"OAP-LAB:{uuid4()}:v1",
            body="{}", notebook_id=str(uuid4()), version=1, digest="a" * 64,
        )
    assert connection.committed is False


def test_missing_or_tampered_audit_receipt_blocks_reopen(store):
    owner = str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    receipts = store._lab_receipts[(owner, notebook.identifier)]
    original = receipts.pop()
    with pytest.raises(lab.NotebookHistoryUnavailable, match="receipt_missing"):
        lab.reopen(owner, notebook.identifier)
    receipts.append(original)
    receipts[0]["metadata"]["digest"] = "f" * 64
    with pytest.raises(lab.NotebookHistoryUnavailable, match="receipt_mismatch"):
        lab.reopen(owner, notebook.identifier)


def test_duplicate_audit_receipt_blocks_reopen(store):
    owner = str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    receipts = store._lab_receipts[(owner, notebook.identifier)]
    receipts.append(dict(receipts[0]))
    with pytest.raises(lab.NotebookHistoryUnavailable, match="receipt_duplicate"):
        lab.reopen(owner, notebook.identifier)


def test_independent_recovery_restores_without_primary_workspace(store):
    owner = str(uuid4())
    notebook = _notebook()
    saved = lab.save(owner, notebook)
    assert saved["independent_recovery_verified"] is True
    store[owner].clear()
    store._lab_receipts[(owner, notebook.identifier)].clear()
    recovered = lab.recover_from_independent(owner, notebook.identifier)
    assert recovered["independent_recovery_verified"] is True
    assert recovered["notebook"]["question"] == "First question"
    assert recovered["fallback_used"] is False


def test_independent_recovery_wrong_owner_and_tamper_fail_closed(store):
    owner, other = str(uuid4()), str(uuid4())
    notebook = _notebook()
    lab.save(owner, notebook)
    with pytest.raises(lab.NotebookHistoryUnavailable, match="unavailable"):
        lab.recover_from_independent(other, notebook.identifier)
    anchor = store._lab_anchors[(owner, notebook.identifier)][0]
    anchor["payload"]["entry"]["notebook"]["question"] = "forged"
    with pytest.raises(lab.NotebookHistoryUnavailable, match="tampered"):
        lab.recover_from_independent(owner, notebook.identifier)


def test_primary_save_survives_independent_recovery_outage(store, monkeypatch):
    owner = str(uuid4())
    notebook = _notebook()
    monkeypatch.setattr(
        lab.smi_receipt_backend,
        "write_lab_recovery_anchor",
        lambda payload: {
            "ok": False,
            "status": "blocked_independent_hrm_not_proven_separate",
            "receipt_id": None,
            "read_back_ok": False,
            "durable": False,
            "fallback_used": False,
        },
    )
    saved = lab.save(owner, notebook)
    assert saved["workspace_record_persisted"] is True
    assert saved["independent_recovery_verified"] is False
    assert saved["recovery_receipt_id"] is None
