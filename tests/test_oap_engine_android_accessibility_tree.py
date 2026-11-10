from pathlib import Path

SOURCE = Path(
    "android/oapworld/src/main/java/com/onanypostcode/oapworld/OapEngineView.java"
)


def test_android_engine_exposes_bounded_virtual_accessibility_children():
    source = SOURCE.read_text(encoding="utf-8")
    assert "MAX_ACCESSIBILITY_VIRTUAL_ITEMS = 256" in source
    assert "EngineAccessibilityNodeProvider extends AccessibilityNodeProvider" in source
    assert "public AccessibilityNodeProvider getAccessibilityNodeProvider()" in source
    assert "info.addChild(OapEngineView.this, index)" in source
    assert "info.setBoundsInParent(accessibilityBounds(item))" in source


def test_android_engine_virtual_links_expose_click_and_focus_actions():
    source = SOURCE.read_text(encoding="utf-8")
    assert "AccessibilityNodeInfo.ACTION_CLICK" in source
    assert "AccessibilityNodeInfo.ACTION_ACCESSIBILITY_FOCUS" in source
    assert "AccessibilityNodeInfo.ACTION_CLEAR_ACCESSIBILITY_FOCUS" in source
    assert "linkListener.onSafeLink(item.href)" in source
    assert "AccessibilityEvent.TYPE_VIEW_CLICKED" in source


def test_android_engine_virtual_images_expose_image_semantics():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'return "android.widget.ImageView";' in source
    assert 'info.setContentDescription(item.text)' in source
