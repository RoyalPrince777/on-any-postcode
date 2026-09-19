from __future__ import annotations

import threading
import time

import pytest

from mission_control import smi_cancellation
from mission_control import smi_chat_runtime


def test_cancellation_token_is_idempotent_and_secret_safe():
    token = smi_cancellation.new_token("founder")

    assert token.cancelled is False
    assert token.cancel("human_stop") is True
    assert token.cancel("human_stop_again") is False
    snapshot = token.snapshot()

    assert snapshot["cancelled"] is True
    assert snapshot["reason"] == "human_stop"
    assert snapshot["human_authority_final"] is True
    assert snapshot["execution_authority_expanded"] is False
    assert snapshot["private_reasoning_stored"] is False
    with pytest.raises(smi_cancellation.SMIRequestCancelled):
        token.raise_if_cancelled()


def test_closing_smi_stream_cancels_the_active_worker(monkeypatch):
    worker_started = threading.Event()
    worker_cancelled = threading.Event()

    def fake_chat(*args, on_event=None, cancellation_token=None, **kwargs):
        assert cancellation_token is not None
        worker_started.set()
        if on_event is not None:
            on_event({"type": "stage", "stage": "understand", "label": "Understand"})
        try:
            while True:
                cancellation_token.raise_if_cancelled()
                time.sleep(0.005)
        except smi_cancellation.SMIRequestCancelled:
            worker_cancelled.set()
            raise

    monkeypatch.setattr(smi_chat_runtime, "chat", fake_chat)

    events = smi_chat_runtime.chat_events("status", "founder", "Founder")
    first = next(events)
    assert first["type"] == "stage"
    assert worker_started.wait(timeout=1)

    events.close()

    assert worker_cancelled.wait(timeout=1)


def test_normal_smi_stream_completion_is_not_marked_cancelled(monkeypatch):
    def fake_chat(*args, on_event=None, cancellation_token=None, **kwargs):
        assert cancellation_token is not None
        cancellation_token.raise_if_cancelled()
        return {"request_id": "req-1", "response": "ok"}

    monkeypatch.setattr(smi_chat_runtime, "chat", fake_chat)

    events = list(smi_chat_runtime.chat_events("status", "founder", "Founder"))

    assert events[-1]["type"] == "complete"
    assert events[-1]["result"]["response"] == "ok"
    assert not any(item["type"] == "cancelled" for item in events)
