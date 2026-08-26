from __future__ import annotations

from http import HTTPStatus

from mission_control import organism_service


class _Process:
    def __init__(self, returncode):
        self.returncode = returncode

    def poll(self):
        return self.returncode


def test_health_is_green_only_while_worker_process_is_alive():
    status, payload = organism_service._health_payload(_Process(None))
    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["worker_alive"] is True
    assert payload["human_authority_final"] is True
    assert payload["independent_execution"] is False
    assert payload["consequential_control_surface"] is False

    status, payload = organism_service._health_payload(_Process(2))
    assert status == HTTPStatus.SERVICE_UNAVAILABLE
    assert payload["ok"] is False
    assert payload["worker_alive"] is False


def test_invalid_port_fails_to_safe_default(monkeypatch):
    monkeypatch.setenv("PORT", "not-a-port")
    assert organism_service._port() == 10000
    monkeypatch.setenv("PORT", "70000")
    assert organism_service._port() == 10000
