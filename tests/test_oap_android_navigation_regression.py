"""Focused source-level regression checks for merged Android navigation fixes.

These tests do not execute an Android Activity or prove APK/device behaviour.
"""
from pathlib import Path
import re

ROOT = Path("android/oapworld/src/main/java/com/onanypostcode/oapworld")
ACTIVITY = ROOT / "MainActivity.java"
CLIENT = ROOT / "EngineDocumentClient.java"


def method_body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    raise AssertionError(f"Unclosed method: {signature}")


def test_native_back_history_and_root_exit_remain_distinct():
    source = ACTIVITY.read_text(encoding="utf-8")
    body = method_body(source, "public void onBackPressed()")
    history = body.index("engineActive && engineHistoryIndex > 0")
    decrement = body.index("engineHistoryIndex--;")
    history_open = body.index("openFirstPartyPath(engineHistory.get(engineHistoryIndex), false);")
    root = body.index("else if (engineActive)")
    exit_activity = body.index("super.onBackPressed();")
    webview_back = body.index("webView.goBack();")
    assert history < decrement < history_open < root < exit_activity < webview_back
    assert "showWebViewFallback()" not in body


def test_webview_transition_invalidates_before_visibility_or_load():
    source = ACTIVITY.read_text(encoding="utf-8")
    body = method_body(source, "private void loadWebViewUrl(String url)")
    assert body.index("engineClient.cancelPending();") < body.index("showWebViewFallback();")
    assert body.index("showWebViewFallback();") < body.index("webView.loadUrl(url);")


def test_all_async_native_delivery_paths_check_generation():
    source = CLIENT.read_text(encoding="utf-8")
    cancel = method_body(source, "public void cancelPending()")
    assert "generation.incrementAndGet();" in cancel
    fetch = method_body(source, "public void fetch(")
    search = method_body(source, "public void submitCertifiedSearch(")
    fallback = method_body(source, "private void postFallback(")
    for body in (fetch, search, fallback):
        assert "generation.get() == requestGeneration" in body
    assert "callback.onEngineDocument(body, sourcePath)" in fetch
    assert "callback.onEngineDocument(responseBody, resolvedPath)" in search
    assert "callback.onFallback(sourcePath)" in fallback


def test_native_back_button_disables_at_root_without_changing_system_back():
    source = ACTIVITY.read_text(encoding="utf-8")
    refresh = method_body(source, "private void refreshNavigationState()")
    assert "backButton.setEnabled(engineHistoryIndex > 0);" in refresh
    back = method_body(source, "public void onBackPressed()")
    assert "super.onBackPressed();" in back
