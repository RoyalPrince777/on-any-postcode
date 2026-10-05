from pathlib import Path

import pytest

from oap.browser_engine import (
    CookieJar,
    ResponseCache,
    build_request,
    parse_css_color,
    render_html,
)
from oap.browser_engine.cache import MAX_CACHE_ENTRY_BYTES


def test_paint_parser_accepts_bounded_colors_and_bold_output():
    assert parse_css_color("#abc") == "#AABBCC"
    assert parse_css_color("#12abef") == "#12ABEF"
    assert parse_css_color("gold") == "#FFD700"
    assert parse_css_color("rgb(1,2,3)") is None

    document = render_html(
        "<style>.hero{color:#123456;background-color:gold;font-weight:700}</style>"
        "<p class='hero'>Styled OAP</p>",
        viewport_width=320,
    )
    item = document.items[0]
    assert item.color == "#123456"
    assert item.background_color == "#FFD700"
    assert item.bold is True


def test_android_native_engine_draws_paint_fields_without_arbitrary_color_input():
    source = Path(
        "android/oapworld/src/main/java/com/onanypostcode/oapworld/OapEngineView.java"
    ).read_text(encoding="utf-8")
    assert 'value.matches("^#[0-9A-Fa-f]{6}$")' in source
    assert "backgroundPaint.setColor(Color.parseColor(item.backgroundColor))" in source
    assert "textPaint.setFakeBoldText(item.bold)" in source


def test_response_cache_is_bounded_and_lru():
    cache = ResponseCache(max_bytes=MAX_CACHE_ENTRY_BYTES * 2)
    first = b"a" * MAX_CACHE_ENTRY_BYTES
    second = b"b" * MAX_CACHE_ENTRY_BYTES
    third = b"c" * MAX_CACHE_ENTRY_BYTES
    cache.put("https://oap.example/1", first, content_type="text/html")
    cache.put("https://oap.example/2", second, content_type="text/html")
    assert cache.get("https://oap.example/1") is not None
    cache.put("https://oap.example/3", third, content_type="text/html")
    assert cache.get("https://oap.example/2") is None
    assert cache.get("https://oap.example/1") is not None
    assert cache.get("https://oap.example/3") is not None


def test_response_cache_rejects_oversized_entry_and_non_web_url():
    cache = ResponseCache()
    with pytest.raises(ValueError, match="cache_entry_too_large"):
        cache.put(
            "https://oap.example/large",
            b"x" * (MAX_CACHE_ENTRY_BYTES + 1),
            content_type="text/plain",
        )
    with pytest.raises(ValueError):
        cache.put("file:///tmp/x", b"x", content_type="text/plain")


def test_cookie_jar_is_host_origin_path_and_secure_bounded():
    jar = CookieJar()
    jar.set_cookie(
        "https://oap.example/account",
        "sid=abc; Path=/; Secure; HttpOnly; SameSite=Lax",
    )
    assert jar.cookie_header("https://oap.example/") == ""
    assert jar.cookie_header("https://oap.example/", include_http_only=True) == "sid=abc"
    assert jar.cookie_header("http://oap.example/", include_http_only=True) == ""
    assert jar.cookie_header("https://other.example/", include_http_only=True) == ""


def test_cookie_jar_rejects_cross_host_domain_and_insecure_samesite_none():
    jar = CookieJar()
    with pytest.raises(ValueError, match="cross_host_cookie_domain_not_supported"):
        jar.set_cookie("https://oap.example/", "sid=x; Domain=evil.example")
    with pytest.raises(ValueError, match="samesite_none_requires_secure"):
        jar.set_cookie("https://oap.example/", "sid=x; SameSite=None")



def test_network_request_policy_allows_only_bounded_web_requests_and_same_origin_credentials():
    request = build_request(
        "https://oap.example/api",
        method="POST",
        body=b"ok",
        initiator_url="https://oap.example/world",
    )
    assert request.include_credentials is True

    cross_origin = build_request(
        "https://other.example/api",
        initiator_url="https://oap.example/world",
    )
    assert cross_origin.include_credentials is False

    with pytest.raises(ValueError, match="unsupported_request_method"):
        build_request("https://oap.example/api", method="DELETE")
    with pytest.raises(ValueError, match="request_body_not_allowed"):
        build_request("https://oap.example/api", method="GET", body=b"x")
    with pytest.raises(ValueError):
        build_request("file:///tmp/x")
