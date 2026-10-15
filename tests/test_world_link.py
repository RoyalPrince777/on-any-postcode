import pytest

from mission_control.world_link import validate_world_link


def test_public_https_link_is_reference_only():
    item = validate_world_link("https://example.com/post?id=42")
    assert item["url"] == "https://example.com/post?id=42"
    assert item["source_host"] == "example.com"
    assert item["sharing_mode"] == "external_link_only"
    assert item["embed_authorised"] == "unverified"
    assert item["republication_authorised"] == "unverified"


@pytest.mark.parametrize("url", [
    "http://example.com/post",
    "javascript:alert(1)",
    "https://localhost/private",
    "https://127.0.0.1/private",
    "https://[::1]/",
    "https://user:pass@example.com/",
    "https://example.com:8080/",
    "https://example.com/#fragment",
    "https://example.com/\nHeader: injected",
    "https://example.com/" + "x" * 2050,
])
def test_world_link_rejects_unsafe_or_unverified_forms(url):
    with pytest.raises(ValueError, match="invalid_world_link"):
        validate_world_link(url)
