from mission_control import web_security


def test_private_smi_chat_burst_cap_allows_active_conversation():
    limiter = web_security.CHAT_BURST_LIMITER
    assert limiter.limit == 30
    assert limiter.window_seconds == 60
    assert limiter.duplicate_seconds == 1.0


def test_duplicate_retry_does_not_consume_extra_slot(monkeypatch):
    times = iter((100.0, 100.5, 101.5, 102.5))
    monkeypatch.setattr(web_security.time, "monotonic", lambda: next(times))
    limiter = web_security.SlidingWindowLimiter(
        limit=3,
        window_seconds=60,
        duplicate_seconds=1.0,
    )

    assert limiter.allow("founder") is True
    assert limiter.allow("founder") is True  # coalesced duplicate
    assert limiter.allow("founder") is True
    assert limiter.allow("founder") is True
