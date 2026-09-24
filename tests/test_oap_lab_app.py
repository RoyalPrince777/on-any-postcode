"""Private OAP LAB app: proof of access control and transient research-only behaviour."""
import app as app_module
from mission_control import web_security


def _client(monkeypatch, *, founder=True):
    monkeypatch.setattr(
        web_security, "current_authenticated_user",
        lambda: {"id": "11111111-1111-4111-8111-111111111111", "name": "Founder"}
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
    assert b"does not save notebooks" in result.data
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
    assert b"STOP: experiment not run" in result.data
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
