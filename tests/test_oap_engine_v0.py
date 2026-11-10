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



def test_oap_engine_main_path_applies_stylesheet_layout():
    document = render_html(
        "<html><head><title>Styled</title><style>"
        "#lead { margin: 12px; padding: 8px; font-size: 24px; text-align:center }"
        ".hidden { display:none }"
        "</style></head><body>"
        "<p id='lead'>Centered OAP</p>"
        "<p class='hidden'>Do not render</p>"
        "</body></html>",
        viewport_width=320,
    )

    assert document.title == "Styled"
    assert [item.text for item in document.items] == ["Centered OAP"]
    item = document.items[0]
    assert item.height == 32
    assert item.x > 36


def test_oap_engine_inline_style_overrides_stylesheet_in_layout_path():
    document = render_html(
        "<style>p { font-size: 12px; margin: 2px }</style>"
        "<p style='font-size:30px;margin:10px'>Large text</p>",
        viewport_width=320,
    )

    assert len(document.items) == 1
    assert document.items[0].height == 38
    assert document.items[0].x == 26


def test_oap_engine_link_href_propagates_through_nested_dom():
    document = render_html(
        "<p><a href='https://example.com'><strong>Open web</strong></a></p>",
        viewport_width=320,
    )
    assert len(document.items) == 1
    assert document.items[0].kind == "link"
    assert document.items[0].href == "https://example.com"
