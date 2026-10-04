from oap.browser_engine.css import computed_style, parse_stylesheet
from oap.browser_engine.dom import parse_html_document


def test_dom_builds_parent_child_tree_and_hides_script_text_from_content():
    root = parse_html_document(
        "<main id='world'><section class='card hero'><h1>OAP World</h1>"
        "<p>One Front Door</p><script>bad()</script></section></main>"
    )
    main = root.children[0]
    section = main.children[0]

    assert main.tag == "main"
    assert main.id == "world"
    assert section.classes == frozenset({"card", "hero"})
    assert section.parent is main
    assert section.text_content() == "OAP World One Front Door"


def test_dom_recovers_from_mismatched_end_tags_without_losing_document():
    root = parse_html_document("<div><p>Hello</div><p>World</p>")
    assert "Hello" in root.text_content()
    assert "World" in root.text_content()


def test_css_cascade_prefers_id_over_class_over_tag_and_inline_over_all():
    root = parse_html_document(
        "<p id='lead' class='hero' style='font-weight:900'>Hello</p>"
    )
    node = root.children[0]
    rules = parse_stylesheet(
        "p { color: white; font-weight:400 }"
        ".hero { color: green }"
        "#lead { color: gold }"
    )
    style = computed_style(node, rules)

    assert style["color"] == "gold"
    assert style["font-weight"] == "900"


def test_css_ignores_unsupported_properties_and_complex_selectors_in_v0():
    rules = parse_stylesheet(
        "p { position:fixed; color:white }"
        "main p { color:red }"
        ".card:hover { color:blue }"
    )
    assert len(rules) == 1
    assert rules[0].selector == "p"
    assert rules[0].declarations == (("color", "white"),)
