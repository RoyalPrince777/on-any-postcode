from pathlib import Path

VIEW = Path(
    "android/oapworld/src/main/java/com/onanypostcode/oapworld/OapEngineView.java"
)
STORAGE = Path(
    "android/oapworld/src/main/java/com/onanypostcode/oapworld/EngineOriginStorage.java"
)


def test_android_engine_consumes_bounded_accessibility_summary():
    source = VIEW.read_text(encoding="utf-8")
    assert "MAX_ACCESSIBILITY_SUMMARY_NODES = 50" in source
    assert "MAX_ACCESSIBILITY_SUMMARY_CHARS = 4096" in source
    assert 'document.optJSONArray("accessibility")' in source
    assert "setContentDescription(accessibilitySummary(" in source
    assert "setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES)" in source


def test_android_engine_origin_storage_is_durable_and_quota_bounded():
    source = STORAGE.read_text(encoding="utf-8")
    assert 'getSharedPreferences(STORE_NAME, Context.MODE_PRIVATE)' in source
    assert "ORIGIN_QUOTA_BYTES = 64 * 1024" in source
    assert "MAX_KEYS_PER_ORIGIN = 256" in source
    assert "MAX_KEY_BYTES = 256" in source
    assert "MAX_VALUE_BYTES = 16 * 1024" in source
    assert '"https".equals(scheme)' in source
    assert '"http".equals(scheme)' in source
    assert 'throw new IllegalArgumentException("unsupported_origin_scheme")' in source
    assert 'throw new IllegalStateException("origin_storage_quota_exceeded")' in source


def test_android_engine_origin_storage_namespaces_by_normalized_origin():
    source = STORAGE.read_text(encoding="utf-8")
    assert 'return scheme + "://" + host.toLowerCase(Locale.ROOT) + ":" + port;' in source
    assert 'return origin(rawUrl) + "|";' in source
    assert "preferences.edit().putString(targetKey, cleanValue).apply()" in source
    assert "public synchronized void clearOrigin(String rawUrl)" in source
