from flask import Flask, request

from mission_control.surface_security import OAPRequest, _SHARE_REQUEST_MAX_BYTES


def _app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
    app.request_class = OAPRequest
    return app


def test_share_upload_gets_transport_overhead_without_widening_global_cap():
    app = _app()

    with app.test_request_context("/linkup/share", method="POST"):
        assert request.max_content_length == _SHARE_REQUEST_MAX_BYTES
        assert request.max_content_length == 26 * 1024 * 1024

    with app.test_request_context("/linkup/voice", method="POST"):
        assert request.max_content_length == 8 * 1024 * 1024

    with app.test_request_context("/", method="POST"):
        assert request.max_content_length == 8 * 1024 * 1024


def test_share_transport_override_accepts_trailing_slash_only_for_post():
    app = _app()

    with app.test_request_context("/linkup/share/", method="POST"):
        assert request.max_content_length == _SHARE_REQUEST_MAX_BYTES

    with app.test_request_context("/linkup/share", method="GET"):
        assert request.max_content_length == 8 * 1024 * 1024
