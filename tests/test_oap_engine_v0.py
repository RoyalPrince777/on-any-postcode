from oap import android_platform
from oap.browser_engine import render_html


def test_oap_engine_owns_html_to_display_list_path():
    document = render_html(
        "<html><head><title>OAP Test</title></head>"
        "<body><h1>One World</h1><p>One Front Door</p>"
        "<a href='https://example.com'>Open web</a>"
        "<script>steal()</script></body></html>",
        viewport_width=320,
    )
    assert document.title == "OAP Test"
    text = " ".join(item.text for item in document.items)
    assert "One World" in text
    assert "One Front Door" in text
    assert "Open web" in text
    assert "steal()" not in text
    assert any(item.kind == "link" and item.href == "https://example.com" for item in document.items)


def test_oap_engine_wraps_and_produces_deterministic_geometry():
    document = render_html("<p>" + ("word " * 80) + "</p>", viewport_width=200)
    assert len(document.items) > 1
    assert all(item.x == 16 for item in document.items)
    assert all(item.height == 24 for item in document.items)
    assert [item.y for item in document.items] == sorted(item.y for item in document.items)


def test_oap_engine_rejects_unusable_viewport():
    try:
        render_html("<p>x</p>", viewport_width=100)
    except ValueError as exc:
        assert "viewport_width" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_oap_android_truth_boundary_does_not_fake_custom_rom():
    state = android_platform.status()
    assert state["custom_android_os_exists"] is False
    assert state["oap_rendering_engine_standards_complete"] is False
    assert state["generation_0"]["renderer"] == "Android System WebView"
    assert state["generation_1"]["status"] == "ARCHITECTURE_ONLY"
