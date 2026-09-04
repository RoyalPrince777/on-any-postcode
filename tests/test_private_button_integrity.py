from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

from werkzeug.exceptions import MethodNotAllowed, NotFound
from werkzeug.routing import RequestRedirect

import app as app_module
from mission_control import autonomy_levels

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "mission_control" / "templates"
URL_FOR_RE = re.compile(r"url_for\(\s*['\"]([^'\"]+)['\"]")
LITERAL_ATTR_RE = re.compile(
    r"(?P<attr>href|action|data-endpoint|data-json-endpoint)=['\"](?P<value>/[^'\"]*)['\"]"
)
PUBLIC_ORIGIN = "https://on-any-postcode.onrender.com"


def _templates():
    return tuple(sorted(TEMPLATE_ROOT.rglob("*.html")))


def _clean_literal_path(value: str) -> str | None:
    if any(marker in value for marker in ("{{", "${", "<", ">")):
        return None
    return urlsplit(value).path or "/"


def _registered_methods(path: str) -> set[str]:
    methods: set[str] = set()
    adapter = app_module.app.url_map.bind("example.test")
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        try:
            adapter.match(path, method=method)
        except RequestRedirect:
            methods.add(method)
        except (MethodNotAllowed, NotFound):
            continue
        else:
            methods.add(method)
    return methods


def test_all_private_template_url_for_endpoints_are_registered():
    referenced: set[str] = set()
    for template in _templates():
        referenced.update(URL_FOR_RE.findall(template.read_text(encoding="utf-8")))

    missing = sorted(referenced - set(app_module.app.view_functions))
    assert missing == []


def test_all_literal_private_control_paths_resolve_to_registered_routes():
    failures: list[str] = []
    for template in _templates():
        text = template.read_text(encoding="utf-8")
        for match in LITERAL_ATTR_RE.finditer(text):
            path = _clean_literal_path(match.group("value"))
            if path is None:
                continue
            methods = _registered_methods(path)
            if not methods:
                failures.append(f"{template.relative_to(ROOT)}: {match.group('attr')}={path}")
    assert failures == []


def test_data_action_buttons_have_post_routes():
    failures: list[str] = []
    for template in _templates():
        text = template.read_text(encoding="utf-8")
        for match in LITERAL_ATTR_RE.finditer(text):
            if match.group("attr") not in {"data-endpoint", "data-json-endpoint"}:
                continue
            path = _clean_literal_path(match.group("value"))
            if path is None:
                continue
            if "POST" not in _registered_methods(path):
                failures.append(f"{template.relative_to(ROOT)}: POST {path}")
    assert failures == []


def test_private_operator_surfaces_use_real_public_origin():
    directly_linked_templates = (
        TEMPLATE_ROOT / "mission.html",
        TEMPLATE_ROOT / "travel_supply_control.html",
        TEMPLATE_ROOT / "mission_control" / "infrastructure.html",
    )
    for template in directly_linked_templates:
        text = template.read_text(encoding="utf-8")
        assert 'href="/"' not in text, template.name
        assert f'href="{PUBLIC_ORIGIN}/' in text, template.name

    smi_wrapper = (TEMPLATE_ROOT / "ollama_chat.html").read_text(encoding="utf-8")
    assert f"const publicOapOrigin='{PUBLIC_ORIGIN}/'" in smi_wrapper
    assert "publicFrontDoor.href=publicOapOrigin" in smi_wrapper


def test_a4_is_bounded_and_does_not_expand_runtime_authority(monkeypatch):
    monkeypatch.setenv("OAP_AUTONOMY_LEVEL", "A4")
    status = autonomy_levels.status()

    assert status["configured_level"] == "A4"
    assert status["a3_execution_enabled"] is True
    assert status["a3_policy_ready"] is True
    assert status["a4_policy_ready"] is True
    assert status["a4_enabled"] is True
    assert set(status["a4_workflow_actions"]) == {
        "RUNTIME_HEARTBEAT",
        "RUNTIME_HEALTH_PROBE",
    }
    assert status["a4_max_workflow_steps"] == 21
    assert status["a4_checkpoint_every"] == 3
    assert status["a4_expands_action_authority"] is False
    assert status["a5_enabled"] is False
    assert status["consequential_action_allowed"] is False
    assert status["human_authority_final"] is True
