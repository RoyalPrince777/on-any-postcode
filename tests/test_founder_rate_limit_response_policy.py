from flask import Flask, request

from mission_control import web_security


def _policy_app(limiter):
    app = Flask(__name__)

    @app.post("/sign-in/<int:status_code>")
    def sign_in(status_code):
        key = f"auth:sign-in:{request.remote_addr or 'unknown'}"
        if not limiter.allow(key):
            return "blocked", 429
        if status_code == 200:
            limiter.reset_key(key)
        return "result", status_code

    @app.post("/activation/<int:status_code>")
    def activation(status_code):
        key = f"auth:activation:{request.remote_addr or 'unknown'}"
        if not limiter.allow(key):
            return "blocked", 429
        return "result", status_code

    return app


def test_repeated_infrastructure_failures_never_become_local_429():
    limiter = web_security.SlidingWindowLimiter(
        limit=2,
        window_seconds=300,
        duplicate_seconds=0.0,
        fingerprint_request_body=True,
    )
    client = _policy_app(limiter).test_client()

    for attempt in range(5):
        response = client.post("/sign-in/503", data={"attempt": str(attempt)})
        assert response.status_code == 503


def test_only_distinct_401_sign_in_failures_fill_the_window():
    limiter = web_security.SlidingWindowLimiter(
        limit=2,
        window_seconds=300,
        duplicate_seconds=5.0,
        fingerprint_request_body=True,
    )
    client = _policy_app(limiter).test_client()

    assert client.post("/sign-in/401", data={"password": "bad-one"}).status_code == 401
    assert client.post("/sign-in/401", data={"password": "bad-two"}).status_code == 401
    assert client.post("/sign-in/401", data={"password": "bad-three"}).status_code == 429


def test_exact_duplicate_401_double_submit_is_coalesced():
    limiter = web_security.SlidingWindowLimiter(
        limit=2,
        window_seconds=300,
        duplicate_seconds=5.0,
        fingerprint_request_body=True,
    )
    client = _policy_app(limiter).test_client()

    assert client.post("/sign-in/401", data={"password": "same-bad"}).status_code == 401
    assert client.post("/sign-in/401", data={"password": "same-bad"}).status_code == 401
    assert client.post("/sign-in/401", data={"password": "different-bad"}).status_code == 401
    assert client.post("/sign-in/401", data={"password": "third-distinct"}).status_code == 429


def test_success_clears_failed_sign_in_history():
    limiter = web_security.SlidingWindowLimiter(
        limit=2,
        window_seconds=300,
        duplicate_seconds=0.0,
        fingerprint_request_body=True,
    )
    client = _policy_app(limiter).test_client()

    assert client.post("/sign-in/401", data={"password": "bad-one"}).status_code == 401
    assert client.post("/sign-in/200", data={"password": "correct"}).status_code == 200
    assert client.post("/sign-in/401", data={"password": "bad-two"}).status_code == 401
    assert client.post("/sign-in/401", data={"password": "bad-three"}).status_code == 401
    assert client.post("/sign-in/401", data={"password": "bad-four"}).status_code == 429


def test_non_401_sign_in_errors_do_not_consume_failure_budget():
    limiter = web_security.SlidingWindowLimiter(
        limit=1,
        window_seconds=300,
        duplicate_seconds=0.0,
        fingerprint_request_body=True,
    )
    client = _policy_app(limiter).test_client()

    assert client.post("/sign-in/400", data={"attempt": "one"}).status_code == 400
    assert client.post("/sign-in/403", data={"attempt": "two"}).status_code == 403
    assert client.post("/sign-in/502", data={"attempt": "three"}).status_code == 502
    assert client.post("/sign-in/401", data={"password": "bad"}).status_code == 401
    assert client.post("/sign-in/401", data={"password": "different"}).status_code == 429


def test_activation_scope_keeps_existing_non_5xx_accounting_policy():
    limiter = web_security.SlidingWindowLimiter(
        limit=1,
        window_seconds=300,
        duplicate_seconds=0.0,
        fingerprint_request_body=True,
    )
    client = _policy_app(limiter).test_client()

    assert client.post("/activation/503", data={"attempt": "infra"}).status_code == 503
    assert client.post("/activation/403", data={"attempt": "bad-proof"}).status_code == 403
    assert client.post("/activation/403", data={"attempt": "another-proof"}).status_code == 429
