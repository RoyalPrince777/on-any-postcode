import random
import string

import pytest

from oap.browser_engine import render_html
from oap.browser_engine.dom import MAX_HTML_CHARS


def _malformed_html(seed: int) -> str:
    rng = random.Random(seed)
    tags = ["div", "p", "span", "a", "section", "main", "nav", "h1", "style"]
    parts = []
    for _ in range(80):
        choice = rng.randrange(5)
        tag = rng.choice(tags)
        if choice == 0:
            parts.append(f"<{tag}>")
        elif choice == 1:
            parts.append(f"</{tag}>")
        elif choice == 2:
            parts.append("<" + "".join(rng.choice(string.ascii_letters) for _ in range(8)))
        elif choice == 3:
            parts.append("&" + "".join(rng.choice(string.ascii_letters) for _ in range(6)))
        else:
            parts.append("".join(rng.choice(string.ascii_letters + " ") for _ in range(24)))
    return "".join(parts)


def test_oap_engine_survives_deterministic_malformed_html_corpus():
    for seed in range(250):
        document = render_html(_malformed_html(seed), viewport_width=320)
        assert document.width == 320
        assert document.height > 0
        assert len(document.items) < 5000


def test_oap_engine_contract_carries_semantics_and_forms():
    document = render_html(
        "<main><h1>OAP</h1><a href='/search'>Search</a>"
        "<form action='/search'><input name='q' required></form></main>",
        viewport_width=320,
        base_url="https://on-any-postcode.onrender.com/",
    ).to_dict()

    assert any(node["role"] == "heading" and node["name"] == "OAP" for node in document["accessibility"])
    assert any(node["role"] == "link" and node["name"] == "Search" for node in document["accessibility"])
    assert len(document["forms"]) == 1
    assert document["forms"][0]["action"] == "https://on-any-postcode.onrender.com/search"


def test_oap_engine_fails_closed_before_parsing_oversized_html():
    with pytest.raises(ValueError, match="html_input_too_large"):
        render_html("x" * (MAX_HTML_CHARS + 1), viewport_width=320)
