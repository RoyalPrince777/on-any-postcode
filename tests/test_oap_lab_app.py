"""Private OAP LAB app: proof of access control and transient research-only behaviour."""
import app as app_module
from mission_control import web_security


def _client(monkeypatch, *, founder=True):
    monkeypatch.setattr(
        web_security, "current_authenticated_user",
        lambda: {"id": "11111111-1111-4111-8111-111111111111", "name": "Founder", "email": "founder@example.test"}
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: founder)
    return app_module.app.test_client()


def _form(**values):
    data = {
        "csrf_token": "a" * 48,
        "mission": "debt_dependency",
        "domain": "artificial_intelligence",
        "question": "Can this claim be checked?",
        "hypothesis": "Synthetic mean is four.",
        "falsification": "Mean differs from four.",
        "operation": "mean",
        "dataset": "2, 4, 6",
        "synthetic": "yes",
        "human_approved": "yes",
    }
    data.update(values)
    return data


def test_lab_requires_authenticated_founder(monkeypatch):
    client = _client(monkeypatch, founder=False)
    assert client.get("/oap-lab").status_code == 403


def test_lab_is_private_review_only_and_not_cached(monkeypatch):
    client = _client(monkeypatch)
    result = client.get("/oap-lab")
    assert result.status_code == 200
    assert result.headers["Cache-Control"] == "no-store"
    assert b"OAP LAB" in result.data
    assert b"Ordinary workspace records are not proven immutable" in result.data
    assert b"21" in result.data


def test_lab_csrf_fails_closed(monkeypatch):
    client = _client(monkeypatch)
    assert client.post("/oap-lab", data=_form()).status_code == 403


def test_lab_synthetic_arithmetic_never_claims_persistence(monkeypatch):
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    result = client.post("/oap-lab", data=_form())
    assert result.status_code == 200
    assert b"SMI review finalised" in result.data
    assert b"4.0" in result.data
    assert b"Not saved" in result.data
    assert b"Not scientific proof" in result.data


def test_lab_stop_blocks_experiment(monkeypatch):
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    result = client.post("/oap-lab", data=_form(stopped="yes"))
    assert b"STOP: notebook review not run" in result.data
    assert b"SMI review finalised" not in result.data


def test_lab_rejects_nonsynthetic_and_live_actions(monkeypatch):
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    for data in (_form(synthetic=""), _form(operation="external_io")):
        result = client.post("/oap-lab", data=data)
        assert result.status_code == 200
        assert b"SMI review finalised" not in result.data


def test_organiser_notebook_smi_finalise_is_not_durable(monkeypatch):
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    result = client.post("/oap-lab", data=_form(operation=""))
    assert result.status_code == 200
    assert b"Organiser" in result.data
    assert b"SMI review finalised" in result.data
    assert b"Not saved" in result.data


def test_stop_blocks_notebook_only_review(monkeypatch):
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    result = client.post("/oap-lab", data=_form(operation="", stopped="yes"))
    assert b"STOP: notebook review not run" in result.data
    assert b"SMI review finalised" not in result.data


def test_founder_explicit_export_is_review_only_and_hash_bound(monkeypatch):
    import hashlib
    import json

    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    result = client.post("/oap-lab", data=_form(
        notebook_action="download", operation="",
    ))
    assert result.status_code == 200
    assert result.headers["Cache-Control"] == "no-store"
    assert "attachment;" in result.headers["Content-Disposition"]
    assert result.headers["X-OAP-Notebook-SHA256"] == hashlib.sha256(result.data).hexdigest()
    data = json.loads(result.data)
    assert data["format"] == "oap_lab_review_only_notebook_v1"
    assert data["notebook"]["question"] == "Can this claim be checked?"
    assert data["persisted_by_oap"] is False
    assert data["independently_recoverable"] is False
    assert data["publication_authorised"] is False
    assert data["execution_authorised"] is False


def test_export_requires_founder_csrf_and_unstopped_notebook(monkeypatch):
    client = _client(monkeypatch)
    assert client.post("/oap-lab", data=_form(
        notebook_action="download", operation="",
    )).status_code == 403
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    stopped = client.post("/oap-lab", data=_form(
        notebook_action="download", operation="", stopped="yes",
    ))
    assert "attachment" not in stopped.headers.get("Content-Disposition", "")
    assert b"STOP: notebook review not run" in stopped.data
    invalid = client.post("/oap-lab", data=_form(
        notebook_action="download", operation="external_io",
    ))
    assert "attachment" not in invalid.headers.get("Content-Disposition", "")
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: False)
    assert client.post("/oap-lab", data=_form(
        notebook_action="download", operation="",
    )).status_code == 403


def test_lab_save_reopen_through_existing_workspace(monkeypatch):
    import re

    from mission_control import public_store, workspaces

    records = []

    monkeypatch.setattr(
        public_store, "ensure_authenticated_user", lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        workspaces, "list_records_with_title_prefix",
        lambda owner, workspace, *, title_prefix, limit=100: [
            row for row in reversed(records)
            if row["title"].startswith(title_prefix)
        ][:limit],
    )

    def add(owner, workspace, *, title, body, status):
        assert workspace == "governance"
        assert owner == "11111111-1111-4111-8111-111111111111"
        records.append({"title": title, "body": body, "status": status})
        return "22222222-2222-4222-8222-222222222222"

    monkeypatch.setattr(workspaces, "add_record", add)
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    saved = client.post("/oap-lab", data=_form(
        notebook_action="save", operation="",
    ))
    assert saved.status_code == 200
    assert b"Saved in My World" in saved.data
    assert len(records) == 1
    path = re.search(rb'/oap-lab[?]notebook_id=[a-f0-9-]+', saved.data)
    assert path is not None
    reopened = client.get(path.group().decode().replace("&amp;", "&"))
    assert reopened.status_code == 200
    assert b"Can this claim be checked?" in reopened.data
    assert b"First question" not in reopened.data
    stopped = client.post("/oap-lab", data=_form(
        notebook_action="save", operation="", stopped="yes",
    ))
    assert b"STOP: notebook review not run" in stopped.data
    assert len(records) == 1


def test_lab_store_failure_does_not_claim_saved(monkeypatch):
    from mission_control import public_store, workspaces

    monkeypatch.setattr(
        public_store, "ensure_authenticated_user", lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        workspaces, "list_records_with_title_prefix", lambda *args, **kwargs: [],
    )
    monkeypatch.setattr(
        workspaces, "add_record", lambda *args, **kwargs: (
            (_ for _ in ()).throw(workspaces.WorkspaceUnavailable("offline"))
        ),
    )
    client = _client(monkeypatch)
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    result = client.post("/oap-lab", data=_form(
        notebook_action="save", operation="",
    ))
    assert b"notebook_store_unavailable" in result.data
    assert b"Saved in My World" not in result.data
