from pathlib import Path

MAIN = Path(
    "android/oapworld/src/main/java/com/onanypostcode/oapworld/MainActivity.java"
)
CLIENT = Path(
    "android/oapworld/src/main/java/com/onanypostcode/oapworld/EngineDocumentClient.java"
)


def test_native_search_form_is_visible_only_for_certified_same_origin_get_search():
    source = MAIN.read_text(encoding="utf-8")
    assert '!"GET".equals(form.optString("method"))' in source
    assert '!form.optBoolean("same_origin_action", false)' in source
    assert '"/search".equals(action.getPath())' in source
    assert 'action.getQuery() == null' in source
    assert 'action.getFragment() == null' in source
    assert "certifiedSearchFormActive = true" in source


def test_native_search_form_only_promotes_safe_q_text_control():
    source = MAIN.read_text(encoding="utf-8")
    assert '"q".equals(name)' in source
    assert '!control.optBoolean("disabled", false)' in source
    assert '("text".equals(type) || "search".equals(type))' in source
    assert 'query.length() > 120' in source


def test_native_search_submission_uses_certified_engine_submit_endpoint():
    source = CLIENT.read_text(encoding="utf-8")
    assert 'origin + "/api/oap-engine/submit"' in source
    assert 'payload.put("action", "/search")' in source
    assert 'fields.put("q", safeQuery)' in source
    assert 'connection.setRequestMethod("POST")' in source
    assert '"OAP_ENGINE".equals(renderer)' in source


def test_native_search_submission_keeps_generation_guard():
    source = CLIENT.read_text(encoding="utf-8")
    assert "final int requestGeneration = generation.incrementAndGet();" in source
    assert "if (generation.get() == requestGeneration)" in source
    assert 'callback.onEngineDocument(responseBody, resolvedPath)' in source


def test_main_activity_reuses_single_omnibox_for_certified_search_submit():
    source = MAIN.read_text(encoding="utf-8")
    assert "certifiedSearchFormActive" in source
    assert "submitCertifiedSearchFromOmnibox(input)" in source
    assert "EditorInfo.IME_ACTION_SEARCH" in source
    assert "engineClient.submitCertifiedSearch(query, viewportWidth" in source
    assert "engineFormBar" not in source
    assert "engineSearchButton" not in source
    assert "engineSearchInput" not in source
