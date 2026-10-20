"""Local inference baseline security and bounded result regression tests."""
import pytest

from scripts import oap_local_inference_baseline as baseline


@pytest.mark.parametrize("url", [
    "https://example.com/api/chat",
    "http://example.com:11434/api/chat",
    "http://127.0.0.1:11434/other",
    "http://user:pass@localhost:11434/api/chat",
    "http://localhost:11434/api/chat?remote=1",
])
def test_rejects_nonlocal_or_ambiguous_endpoint(url):
    with pytest.raises(ValueError):
        baseline.benchmark(url, "oap-core:latest")


def test_local_response_metrics(monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, *_args):
            return b'{"message":{"content":"ready"},"eval_count":20,"eval_duration":2000000000}'

    class Opener:
        def open(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr(baseline.request, "build_opener", lambda *_args: Opener())
    result = baseline.benchmark("http://127.0.0.1:11434/api/chat", "oap-core:latest")
    assert result["generation_tokens_per_s"] == 10
    assert result["local_only"] is True
    assert result["production_ready"] is False
    assert "ready" not in result


def test_rejects_redirect():
    with pytest.raises(ValueError, match="redirect"):
        baseline._NoRedirects().redirect_request(None, None, 302, "", {}, "https://example.com")
