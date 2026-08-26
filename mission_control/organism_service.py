"""Render-compatible supervisor for the bounded OAP organism worker.

This module exists only to keep the existing queue worker alive on compute that
expects an HTTP health endpoint. It does not expose job submission, mutation,
approval, or control routes.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

_CHILD: subprocess.Popen[bytes] | None = None


def _port() -> int:
    try:
        value = int(os.environ.get("PORT", "10000"))
    except ValueError:
        return 10000
    return value if 1 <= value <= 65535 else 10000


def _health_payload(child: object | None) -> tuple[int, dict[str, Any]]:
    poll = getattr(child, "poll", None)
    alive = child is not None and callable(poll) and poll() is None
    return (
        HTTPStatus.OK if alive else HTTPStatus.SERVICE_UNAVAILABLE,
        {
            "ok": alive,
            "service": "oap-organism-runtime",
            "worker_alive": alive,
            "human_authority_final": True,
            "independent_execution": False,
            "consequential_control_surface": False,
        },
    )


def _handler(child: subprocess.Popen[bytes]) -> type[BaseHTTPRequestHandler]:
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - HTTP handler API.
            if self.path != "/healthz":
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                return
            status, payload = _health_payload(child)
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    return HealthHandler


def _stop_child(child: subprocess.Popen[bytes]) -> None:
    if child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=25)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=5)


def run() -> int:
    """Supervise one bounded worker and expose health only."""

    global _CHILD
    child = subprocess.Popen(
        [sys.executable, "-m", "mission_control.organism_worker"],
        env=os.environ.copy(),
    )
    _CHILD = child
    server = ThreadingHTTPServer(("0.0.0.0", _port()), _handler(child))

    def request_stop(signum: int, frame: object) -> None:
        del signum, frame
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    try:
        server.serve_forever(poll_interval=0.5)
    except SystemExit:
        pass
    finally:
        server.server_close()
        _stop_child(child)
        _CHILD = None
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
