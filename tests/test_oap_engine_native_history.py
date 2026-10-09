from pathlib import Path

MAIN = Path(
    "android/oapworld/src/main/java/com/onanypostcode/oapworld/MainActivity.java"
)
CLIENT = Path(
    "android/oapworld/src/main/java/com/onanypostcode/oapworld/EngineDocumentClient.java"
)


def test_native_engine_history_has_back_stack_and_truncates_forward_branch():
    source = MAIN.read_text(encoding="utf-8")
    assert "private final List<String> engineHistory = new ArrayList<>();" in source
    assert "private int engineHistoryIndex = -1;" in source
    assert "engineHistoryIndex--;" in source
    assert "openFirstPartyPath(engineHistory.get(engineHistoryIndex), false)" in source
    assert "while (engineHistory.size() > engineHistoryIndex + 1)" in source
    assert "engineHistory.remove(engineHistory.size() - 1)" in source


def test_native_engine_history_records_only_after_valid_engine_document():
    source = MAIN.read_text(encoding="utf-8")
    fetch_index = source.index("engineClient.fetch(path, viewportWidth")
    record_index = source.index("if (recordHistory && sourcePath != null)")
    show_index = source.index("engineView.setDisplayListJson(displayListJson)")
    assert fetch_index < show_index < record_index


def test_native_engine_back_navigation_uses_history_without_forward_toolbar():
    source = MAIN.read_text(encoding="utf-8")
    assert "if (engineActive && engineHistoryIndex > 0)" in source
    assert "engineHistoryIndex--;" in source
    assert "backButton.setEnabled(engineHistoryIndex > 0)" in source
    assert "forwardButton" not in source
    assert "while (engineHistory.size() > engineHistoryIndex + 1)" in source


def test_engine_document_client_suppresses_stale_callbacks_with_generation_token():
    source = CLIENT.read_text(encoding="utf-8")
    assert "private final AtomicInteger generation = new AtomicInteger();" in source
    assert "final int requestGeneration = generation.incrementAndGet();" in source
    assert "if (generation.get() == requestGeneration)" in source
    assert "postFallback(callback, sourcePath, requestGeneration)" in source
    assert "generation.incrementAndGet();" in source
