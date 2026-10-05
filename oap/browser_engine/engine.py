"""OAP Engine v1: bounded first-party DOM/CSS-to-display-list renderer.

This remains intentionally smaller than a standards-complete browser engine.
The important boundary is architectural: the main render path now consumes the
OAP-owned DOM and CSS cascade rather than a parallel flat HTML parser.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass

from .accessibility import AccessibilityNode, build_accessibility_tree
from .css import Rule, computed_style, parse_stylesheet
from .dom import HIDDEN_ELEMENTS, Node, parse_html_document
from .forms import FormModel, extract_forms
from .origin import resolve_http_url
from .paint import is_bold_font_weight, parse_css_color

BLOCK_TAGS = {
    "article",
    "aside",
    "blockquote",
    "body",
    "div",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "section",
    "ul",
}
NON_RENDERED_TAGS = HIDDEN_ELEMENTS | {"head", "title"}


@dataclass(frozen=True)
class DisplayItem:
    kind: str
    text: str
    x: int
    y: int
    width: int
    height: int
    href: str | None = None
    color: str | None = None
    background_color: str | None = None
    bold: bool = False
    src: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RenderDocument:
    title: str
    width: int
    height: int
    items: tuple[DisplayItem, ...]
    accessibility: tuple[AccessibilityNode, ...]
    forms: tuple[FormModel, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "engine": "OAP_ENGINE",
            "contract_version": 1,
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "items": [item.to_dict() for item in self.items],
            "accessibility": [node.to_dict() for node in self.accessibility],
            "forms": [form.to_dict() for form in self.forms],
        }


def _wrap_words(text: str, max_chars: int) -> Iterable[str]:
    words = text.split()
    line = ""
    for word in words:
        candidate = word if not line else f"{line} {word}"
        if len(candidate) <= max_chars:
            line = candidate
            continue
        if line:
            yield line
        while len(word) > max_chars:
            yield word[:max_chars]
            word = word[max_chars:]
        line = word
    if line:
        yield line


def _length_px(value: str | None, default: int = 0) -> int:
    """Parse the bounded integer/px CSS length subset used by Engine v1."""

    if not value:
        return default
    match = re.fullmatch(r"\s*(-?\d{1,4})(?:px)?\s*", value, flags=re.IGNORECASE)
    if match is None:
        return default
    return max(0, min(1000, int(match.group(1))))


def _font_size_px(value: str | None) -> int:
    size = _length_px(value, 16)
    return max(8, min(72, size))


def _box_length(style: dict[str, str], kind: str, side: str) -> int:
    return _length_px(style.get(f"{kind}-{side}"), _length_px(style.get(kind), 0))


def _line_height_px(style: dict[str, str], font_size: int) -> int:
    return max(font_size, _length_px(style.get("line-height"), font_size + 8))


def _attribute_px(node: Node, name: str, default: int) -> int:
    return _length_px(node.attrs.get(name), default)


def _style_rules(root: Node) -> tuple[Rule, ...]:
    chunks = [
        node.text
        for node in root.descendants()
        if node.tag == "style" and node.text
    ]
    return parse_stylesheet("\n".join(chunks))


def _document_title(root: Node) -> str:
    for node in root.descendants():
        if node.tag == "title":
            title = node.text_content().strip()
            if title:
                return title
    return "Untitled"


def _is_block(node: Node, style: dict[str, str]) -> bool:
    display = style.get("display", "").strip().lower()
    if display == "block":
        return True
    if display == "inline":
        return False
    return node.tag in BLOCK_TAGS


def _effective_style(
    node: Node,
    rules: tuple[Rule, ...],
    inherited: dict[str, str],
) -> dict[str, str]:
    style = dict(inherited)
    local = computed_style(node, rules)
    for name in ("color", "font-size", "font-weight", "text-align"):
        if name in local:
            style[name] = local[name]
    for name in (
        "display",
        "margin",
        "margin-top",
        "margin-right",
        "margin-bottom",
        "margin-left",
        "padding",
        "padding-top",
        "padding-right",
        "padding-bottom",
        "padding-left",
        "width",
        "min-width",
        "max-width",
        "line-height",
        "background-color",
    ):
        if name in local:
            style[name] = local[name]
        else:
            style.pop(name, None)
    return style


def render_html(
    html: str,
    viewport_width: int = 390,
    *,
    base_url: str | None = None,
) -> RenderDocument:
    """Render the OAP-owned HTML/DOM/CSS subset to one deterministic contract."""

    if viewport_width < 160:
        raise ValueError("viewport_width must be at least 160")

    root = parse_html_document(html)
    rules = _style_rules(root)

    outer_margin = 16
    content_width = max(1, viewport_width - (outer_margin * 2))
    y = outer_margin
    items: list[DisplayItem] = []

    def render_node(
        node: Node,
        *,
        inherited: dict[str, str],
        inherited_href: str | None,
        x_offset: int,
        available_width: int,
    ) -> None:
        nonlocal y

        if node.tag in NON_RENDERED_TAGS:
            return

        style = _effective_style(node, rules, inherited)
        if style.get("display", "").strip().lower() == "none":
            return

        is_block = _is_block(node, style)
        margin_top = _box_length(style, "margin", "top")
        margin_right = _box_length(style, "margin", "right")
        margin_bottom = _box_length(style, "margin", "bottom")
        margin_left = _box_length(style, "margin", "left")
        padding_top = _box_length(style, "padding", "top")
        padding_right = _box_length(style, "padding", "right")
        padding_bottom = _box_length(style, "padding", "bottom")
        padding_left = _box_length(style, "padding", "left")
        font_size = _font_size_px(style.get("font-size"))
        line_height = max(16, _line_height_px(style, font_size))
        char_width = max(4, round(font_size * 0.5))

        outer_available = max(1, available_width - margin_left - margin_right)
        requested_width = _length_px(style.get("width"), outer_available)
        min_width = _length_px(style.get("min-width"), 1)
        max_width = _length_px(style.get("max-width"), outer_available)
        box_width = min(outer_available, max(min_width, min(requested_width, max_width)))
        local_x = x_offset + margin_left + padding_left
        local_width = max(1, box_width - padding_left - padding_right)
        max_chars = max(1, local_width // char_width)
        href = node.attrs.get("href") if node.tag == "a" else inherited_href

        if is_block and items:
            y += margin_top
        y += padding_top

        if node.tag == "img":
            alt = " ".join(node.attrs.get("alt", "").split()) or "Image"
            image_width = min(local_width, _attribute_px(node, "width", min(local_width, 240)))
            image_height = _attribute_px(node, "height", max(80, min(180, image_width)))
            src = resolve_http_url(base_url, node.attrs.get("src", "")) if base_url else None
            items.append(
                DisplayItem(
                    kind="image",
                    text=alt[:2048],
                    x=local_x,
                    y=y,
                    width=image_width,
                    height=image_height,
                    color=parse_css_color(style.get("color")),
                    background_color=parse_css_color(style.get("background-color")),
                    bold=False,
                    src=src,
                )
            )
            y += image_height

        if node.text:
            for line in _wrap_words(node.text, max_chars):
                width = min(local_width, len(line) * char_width)
                align = style.get("text-align", "").strip().lower()
                x = local_x
                if align == "center":
                    x += max(0, (local_width - width) // 2)
                elif align == "right":
                    x += max(0, local_width - width)
                items.append(
                    DisplayItem(
                        kind="link" if href else "text",
                        text=line,
                        x=x,
                        y=y,
                        width=width,
                        height=line_height,
                        href=href,
                        color=parse_css_color(style.get("color")),
                        background_color=parse_css_color(style.get("background-color")),
                        bold=is_bold_font_weight(style.get("font-weight")),
                    )
                )
                y += line_height

        for child in node.children:
            render_node(
                child,
                inherited=style,
                inherited_href=href,
                x_offset=local_x,
                available_width=local_width,
            )

        if is_block and (node.text or node.children or node.tag == "img"):
            y += padding_bottom + margin_bottom

    for child in root.children:
        render_node(
            child,
            inherited={},
            inherited_href=None,
            x_offset=outer_margin,
            available_width=content_width,
        )

    accessibility = build_accessibility_tree(root, rules)
    forms = extract_forms(root, base_url=base_url) if base_url else ()

    return RenderDocument(
        title=_document_title(root),
        width=viewport_width,
        height=max(y + outer_margin, 24 + outer_margin * 2),
        items=tuple(items),
        accessibility=accessibility,
        forms=forms,
    )
