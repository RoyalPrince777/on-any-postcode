"""First-party OAP browser rendering primitives."""

from .accessibility import AccessibilityNode, build_accessibility_tree
from .css import Rule, computed_style, parse_stylesheet
from .dom import Node, parse_html_document
from .engine import DisplayItem, RenderDocument, render_html
from .origin import Origin, parse_origin, resolve_http_url, same_origin
from .storage import OriginStorage

__all__ = [
    "AccessibilityNode",
    "DisplayItem",
    "Node",
    "Origin",
    "OriginStorage",
    "RenderDocument",
    "Rule",
    "build_accessibility_tree",
    "computed_style",
    "parse_html_document",
    "parse_origin",
    "parse_stylesheet",
    "render_html",
    "resolve_http_url",
    "same_origin",
]
