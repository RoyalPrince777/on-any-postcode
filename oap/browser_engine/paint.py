"""Bounded paint-style primitives for OAP Engine."""
from __future__ import annotations

import re

NAMED_COLORS = {
    "black": "#000000",
    "white": "#FFFFFF",
    "red": "#FF0000",
    "green": "#008000",
    "blue": "#0000FF",
    "gold": "#FFD700",
    "gray": "#808080",
    "grey": "#808080",
}


def parse_css_color(value: object) -> str | None:
    raw = str(value or "").strip().lower()
    if not raw or raw == "transparent":
        return None
    if raw in NAMED_COLORS:
        return NAMED_COLORS[raw]
    if re.fullmatch(r"#[0-9a-f]{6}", raw):
        return raw.upper()
    short = re.fullmatch(r"#([0-9a-f])([0-9a-f])([0-9a-f])", raw)
    if short:
        return "#" + "".join(part * 2 for part in short.groups()).upper()
    return None


def is_bold_font_weight(value: object) -> bool:
    raw = str(value or "").strip().lower()
    if raw in {"bold", "bolder"}:
        return True
    if raw.isdigit():
        return int(raw) >= 600
    return False
