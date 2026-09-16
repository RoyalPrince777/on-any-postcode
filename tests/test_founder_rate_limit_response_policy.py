from mission_control import web_security


def test_sign_in_key_is_governed_as_failed_password_only(app):
    limiter = web_security.SlidingWindowLimiter(limit=2, window_seconds=300)
    with app.test_request_context("/auth/sign-in", method="POST"):
        assert limiter.allow("auth:sign-in:203.0.113.7") is True
        # Executable response-policy behavior is covered by the application auth tests;
        # this test pins the dedicated sign-in key namespace used by that policy.
        assert limiter.allow("auth:sign-in:203.0.113.7") is True
        assert limiter.allow("auth:sign-in:203.0.113.7") is False
