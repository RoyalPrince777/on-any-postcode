from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_config():
    path = Path("gunicorn.conf.py")
    spec = importlib.util.spec_from_file_location("oap_gunicorn_config_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_function_health_rechecks_once_after_successful_health(monkeypatch):
    config = _load_config()
    calls: list[object] = []
    worker = object()

    monkeypatch.setattr(config, "_emit_smi_function_health", lambda value: calls.append(value))
    config._FUNCTION_HEALTH_AFTER_HEALTH_EMITTED = False

    config.post_request(
        worker,
        None,
        {"PATH_INFO": "/mission"},
        SimpleNamespace(status="200 OK"),
    )
    config.post_request(
        worker,
        None,
        {"PATH_INFO": "/healthz"},
        SimpleNamespace(status="503 Service Unavailable"),
    )

    assert calls == []
    assert config._FUNCTION_HEALTH_AFTER_HEALTH_EMITTED is False

    config.post_request(
        worker,
        None,
        {"PATH_INFO": "/healthz"},
        SimpleNamespace(status="200 OK"),
    )
    config.post_request(
        worker,
        None,
        {"PATH_INFO": "/healthz"},
        SimpleNamespace(status="200 OK"),
    )

    assert calls == [worker]
    assert config._FUNCTION_HEALTH_AFTER_HEALTH_EMITTED is True
