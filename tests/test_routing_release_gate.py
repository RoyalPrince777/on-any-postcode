"""Execute the actual promotion preflight with bounded check API responses."""
import json
import textwrap
from pathlib import Path
from urllib import request

import pytest

SHA = "a" * 40


def _check(name, **changes):
    return {"id": 1, "name": name, "head_sha": SHA,
            "app": {"slug": "github-actions"}, "status": "completed",
            "conclusion": "success", **changes}


def _execute(monkeypatch, checks):
    source = Path(".github/workflows/runtime-image.yml").read_text()
    step = source.split("name: Require governed checks for exact release SHA", 1)[1].split("      - name:", 1)[0]
    code = textwrap.dedent(step.split("          python - <<'PY'\n", 1)[1].split("\n          PY", 1)[0])
    for key, value in {"REPOSITORY": "owner/repo", "RELEASE_SHA": SHA, "GH_TOKEN": "test-only"}.items():
        monkeypatch.setenv(key, value)
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps({"check_runs": checks}).encode()
    monkeypatch.setattr(request, "urlopen", lambda *args, **kwargs: Response())
    monkeypatch.setattr("time.sleep", lambda *args: None)
    exec(compile(code, "promotion_preflight", "exec"), {})  # noqa: S102 - test the trusted repository workflow itself.


def test_promotion_requires_both_successful_exact_sha_checks(monkeypatch, capsys):
    _execute(monkeypatch, [_check("test"), _check("routing-live-ready")])
    receipt = json.loads(capsys.readouterr().out)
    assert receipt == {"event": "governed_release_gate", "sha": SHA, "success": True}


@pytest.mark.parametrize("conclusion", ["failure", "skipped", "neutral", "cancelled", "timed_out"])
def test_successful_regressions_cannot_override_routing_failure(monkeypatch, conclusion):
    with pytest.raises(SystemExit, match="governed_checks_failed_for_exact_sha"):
        _execute(monkeypatch, [_check("test"), _check("routing-live-ready", conclusion=conclusion)])


@pytest.mark.parametrize("routing", [
    None,
    _check("routing-live-ready", head_sha="b" * 40),
    _check("routing-live-ready", app={"slug": "another-app"}),
    _check("routing-live-ready", status="in_progress", conclusion=None),
])
def test_absent_untrusted_stale_or_pending_routing_cannot_authorise(monkeypatch, routing):
    checks = [_check("test")] + ([] if routing is None else [routing])
    with pytest.raises(SystemExit, match="governed_checks_not_green_for_exact_sha"):
        _execute(monkeypatch, checks)


def test_older_success_cannot_override_newer_failed_routing_attempt(monkeypatch):
    with pytest.raises(SystemExit, match="governed_checks_failed_for_exact_sha"):
        _execute(monkeypatch, [
            _check("test"), _check("routing-live-ready", id=1),
            _check("routing-live-ready", id=2, conclusion="failure"),
        ])
