import pytest

from oap.browser_engine import (
    OriginStorage,
    build_accessibility_tree,
    extract_forms,
    parse_html_document,
    parse_origin,
    parse_stylesheet,
    resolve_http_url,
    same_origin,
)
from oap.browser_engine.css import MAX_CSS_CHARS, MAX_DECLARATIONS_PER_RULE
from oap.browser_engine.dom import MAX_DOM_DEPTH, MAX_HTML_CHARS


def test_origin_model_normalizes_defaults_and_rejects_credentials_or_non_web_schemes():
    origin = parse_origin("https://Example.COM/path?q=1")
    assert origin.serialize() == "https://example.com"
    assert same_origin("https://example.com/a", "https://EXAMPLE.com:443/b")
    assert not same_origin("http://example.com", "https://example.com")
    with pytest.raises(ValueError):
        parse_origin("file:///tmp/test")
    with pytest.raises(ValueError):
        parse_origin("https://user:pass@example.com/")


def test_safe_url_resolution_stays_http_https_only():
    assert resolve_http_url("https://oap.example/world", "/search") == "https://oap.example/search"
    assert resolve_http_url("https://oap.example/world", "https://elsewhere.example/x") == "https://elsewhere.example/x"
    assert resolve_http_url("https://oap.example/world", "javascript:alert(1)") is None


def test_origin_storage_isolated_by_scheme_host_port_and_quota():
    store = OriginStorage(quota_bytes=1024)
    store.set_item("https://oap.example/a", "theme", "dark")
    assert store.get_item("https://oap.example/b", "theme") == "dark"
    assert store.get_item("http://oap.example/", "theme") is None
    assert store.get_item("https://other.example/", "theme") is None
    with pytest.raises(ValueError, match="origin_storage_quota_exceeded"):
        store.set_item("https://oap.example/", "large", "x" * 1010)
    assert store.snapshot("https://oap.example/") == {"theme": "dark"}


def test_accessibility_projection_exposes_landmarks_headings_links_and_controls():
    root = parse_html_document(
        "<main><h1>OAP World</h1><nav><a href='/search'>Search</a></nav>"
        "<button aria-label='Enter'>Go</button><input placeholder='Find OAP'></main>"
    )
    nodes = build_accessibility_tree(root)
    roles = [node.role for node in nodes]
    assert roles == ["main", "heading", "navigation", "link", "button", "textbox"]
    assert nodes[1].name == "OAP World"
    assert nodes[1].level == 1
    assert nodes[3].href == "/search"
    assert nodes[4].name == "Enter"
    assert nodes[5].name == "Find OAP"


def test_accessibility_projection_skips_hidden_and_aria_hidden_content():
    root = parse_html_document(
        "<style>.gone{display:none}</style>"
        "<main><p class='gone'><a href='/x'>Gone</a></p>"
        "<div aria-hidden='true'><button>Hidden</button></div>"
        "<a href='/ok'>Visible</a></main>"
    )
    rules = parse_stylesheet(".gone{display:none}")
    nodes = build_accessibility_tree(root, rules)
    assert [node.name for node in nodes if node.role in {"link", "button"}] == ["Visible"]


def test_dom_parser_enforces_input_and_depth_limits():
    with pytest.raises(ValueError, match="html_input_too_large"):
        parse_html_document("x" * (MAX_HTML_CHARS + 1))

    deep = "<div>" * (MAX_DOM_DEPTH + 2) + "x" + "</div>" * (MAX_DOM_DEPTH + 2)
    with pytest.raises(ValueError, match="dom_depth_limit"):
        parse_html_document(deep)


def test_css_parser_enforces_input_and_declaration_limits():
    with pytest.raises(ValueError, match="css_input_too_large"):
        parse_stylesheet("x" * (MAX_CSS_CHARS + 1))

    declarations = ";".join(f"color:v{i}" for i in range(MAX_DECLARATIONS_PER_RULE + 1))
    with pytest.raises(ValueError, match="css_declaration_limit"):
        parse_stylesheet("p{" + declarations + "}")



def test_form_model_extracts_controls_and_same_origin_action_without_submitting():
    root = parse_html_document(
        "<form method='post' action='/search'>"
        "<input name='q' value='music' required>"
        "<input type='password' name='secret' value='do-not-project'>"
        "<button name='go'>Search</button>"
        "</form>"
    )
    forms = extract_forms(root, base_url="https://on-any-postcode.onrender.com/world")
    assert len(forms) == 1
    form = forms[0]
    assert form.method == "POST"
    assert form.action == "https://on-any-postcode.onrender.com/search"
    assert form.same_origin_action is True
    assert [control.name for control in form.controls] == ["q", "secret", "go"]
    assert form.controls[0].required is True
    assert form.controls[1].control_type == "password"
    assert form.controls[1].value == ""


def test_form_model_marks_cross_origin_action_and_rejects_non_http_action():
    root = parse_html_document(
        "<form action='https://elsewhere.example/pay'><input name='x'></form>"
        "<form action='javascript:alert(1)'><input name='y'></form>"
    )
    forms = extract_forms(root, base_url="https://on-any-postcode.onrender.com/")
    assert forms[0].action == "https://elsewhere.example/pay"
    assert forms[0].same_origin_action is False
    assert forms[1].action is None
    assert forms[1].same_origin_action is False
