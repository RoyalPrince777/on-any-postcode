from pathlib import Path

from oap.browser_engine import parse_html_document, parse_stylesheet, render_html
from oap.browser_engine.css import computed_style


def test_css_supports_compound_descendant_and_child_selectors():
    root = parse_html_document(
        "<main id='world'><section class='card featured'><p class='lead'>Hello</p></section></main>"
    )
    rules = parse_stylesheet(
        "main#world > section.card.featured p.lead { color:#123456; font-weight:700; }"
    )
    paragraph = next(node for node in root.descendants() if node.tag == "p")
    style = computed_style(paragraph, rules)
    assert style["color"] == "#123456"
    assert style["font-weight"] == "700"


def test_css_child_selector_does_not_match_deeper_descendant():
    root = parse_html_document(
        "<main><section><div><p class='lead'>Hello</p></div></section></main>"
    )
    rules = parse_stylesheet("section > p.lead { color:red; }")
    paragraph = next(node for node in root.descendants() if node.tag == "p")
    assert "color" not in computed_style(paragraph, rules)


def test_layout_honours_side_spacing_width_max_width_and_line_height():
    document = render_html(
        "<style>"
        ".box{margin-left:10px;margin-right:20px;padding-left:8px;padding-right:6px;"
        "width:240px;max-width:220px;line-height:30px}"
        "</style><div class='box'>OAP layout depth</div>",
        viewport_width=320,
    )
    item = document.items[0]
    assert item.x >= 34
    assert item.width <= 206
    assert item.height == 30


def test_image_semantics_emit_bounded_display_item_with_safe_source():
    document = render_html(
        "<main><img src='/assets/oap.png' alt='OAP Globe' width='120' height='90'></main>",
        viewport_width=320,
        base_url="https://on-any-postcode.onrender.com/world",
    )
    image = next(item for item in document.items if item.kind == "image")
    assert image.text == "OAP Globe"
    assert image.width == 120
    assert image.height == 90
    assert image.src == "https://on-any-postcode.onrender.com/assets/oap.png"


def test_android_native_view_accepts_image_items_but_only_safe_sources():
    source = Path(
        "android/oapworld/src/main/java/com/onanypostcode/oapworld/OapEngineView.java"
    ).read_text(encoding="utf-8")
    assert '"image".equals(kind)' in source
    assert 'throw new JSONException("unsafe image source scheme")' in source
    assert '"image".equals(item.kind)' in source
