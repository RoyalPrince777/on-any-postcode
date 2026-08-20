from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


class _IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag, attrs):
        del tag
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])


def _duplicate_ids(markup: str) -> set[str]:
    parser = _IdCollector()
    parser.feed(markup)
    counts = Counter(parser.ids)
    return {element_id for element_id, count in counts.items() if count > 1}


def test_home_and_mission_have_no_duplicate_ids(client):
    home = client.get("/").get_data(as_text=True)
    mission = client.get("/mission").get_data(as_text=True)
    organism = client.get("/mission/organism").get_data(as_text=True)

    assert _duplicate_ids(home) == set()
    assert _duplicate_ids(mission) == set()
    assert _duplicate_ids(organism) == set()


def test_navigation_and_authority_landmarks_are_labelled(client):
    home = client.get("/").get_data(as_text=True)
    mission = client.get("/mission").get_data(as_text=True)
    organism = client.get("/mission/organism").get_data(as_text=True)

    assert 'aria-label="Primary navigation"' in home
    assert 'aria-label="Human Authority status"' in home
    assert 'aria-label="Mission Control modes"' in mission
    assert 'aria-current="page"' in mission
    assert 'aria-label="OAP governance law"' in organism
    assert 'aria-label="Human Authority status"' in organism


def test_mobile_layout_rule_is_present():
    css_path = (
        Path(__file__).resolve().parents[1]
        / "mission_control"
        / "static"
        / "mission_control.css"
    )
    css = css_path.read_text(encoding="utf-8")

    assert "@media (max-width: 768px)" in css
    assert ".mc-mode-nav" in css
