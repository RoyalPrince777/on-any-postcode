"""First-party OAP browser rendering primitives."""

from .accessibility import AccessibilityNode, build_accessibility_tree
from .cache import CacheEntry, ResponseCache
from .cookies import Cookie, CookieJar
from .css import Rule, computed_style, parse_stylesheet
from .dom import Node, parse_html_document
from .engine import DisplayItem, RenderDocument, render_html
from .forms import FormControl, FormModel, extract_forms
from .network import NetworkRequest, build_request
from .origin import Origin, parse_origin, resolve_http_url, same_origin
from .paint import is_bold_font_weight, parse_css_color
from .storage import OriginStorage

__all__ = [
    "AccessibilityNode",
    "CacheEntry",
    "Cookie",
    "CookieJar",
    "DisplayItem",
    "FormControl",
    "FormModel",
    "NetworkRequest",
    "Node",
    "Origin",
    "OriginStorage",
    "ResponseCache",
    "RenderDocument",
    "Rule",
    "build_accessibility_tree",
    "build_request",
    "computed_style",
    "extract_forms",
    "is_bold_font_weight",
    "parse_css_color",
    "parse_html_document",
    "parse_origin",
    "parse_stylesheet",
    "render_html",
    "resolve_http_url",
    "same_origin",
]
