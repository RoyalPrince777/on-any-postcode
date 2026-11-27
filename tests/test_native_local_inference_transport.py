import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request
from urllib.error import HTTPError

import pytest

from mission_control import oap_inference_gateway as gateway


def test_local_transport_rejects_redirect_without_following(monkeypatch):
    hits = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(302)
            self.send_header("Location", "/unexpected")
            self.end_headers()

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/api/tags"
        monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
        monkeypatch.setenv("NO_PROXY", "")
        with pytest.raises(HTTPError) as error:
            gateway._read_local_json(request.Request(url), timeout=1)
        assert error.value.code == 302
        assert hits == ["/api/tags"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_model_probe_fails_closed_on_invalid_list(monkeypatch):
    monkeypatch.setattr(gateway, "LOCAL_ENABLED", True)
    monkeypatch.setattr(gateway, "LOCAL_URL", "http://127.0.0.1:11434/api/chat")
    monkeypatch.setattr(gateway, "LOCAL_MODEL", "oap-core:latest")
    monkeypatch.setattr(gateway, "_read_local_json", lambda *_args, **_kw: {"models": None})
    state = gateway.probe_local(force=True)
    assert state["reachable"] is False
    assert state["model_available"] is False
