"""Bounded accessibility-tree projection for OAP Engine DOM."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .css import Rule, computed_style
from .dom import HIDDEN_ELEMENTS, Node

MAX_ACCESSIBILITY_NODES = 5000

LANDMARK_ROLES = {
    "main": "main",
    "nav": "navigation",
    "header": "banner",
    "footer": "contentinfo",
    "form": "form",
}
CONTROL_ROLES = {
    "button": "button",
    "select": "combobox",
    "textarea": "textbox",
}


@dataclass(frozen=True)
class AccessibilityNode:
    role: str
    name: str
    level: int | None = None
    href: str | None = None
    node_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _role(node: Node) -> tuple[str | None, int | None]:
    explicit = node.attrs.get("role", "").strip()
    if explicit:
        return explicit, None
    if node.tag in LANDMARK_ROLES:
        return LANDMARK_ROLES[node.tag], None
    if node.tag in CONTROL_ROLES:
        return CONTROL_ROLES[node.tag], None
    if node.tag == "a" and node.attrs.get("href"):
        return "link", None
    if node.tag in {"ul", "ol"}:
        return "list", None
    if node.tag == "li":
        return "listitem", None
    if node.tag.startswith("h") and len(node.tag) == 2 and node.tag[1].isdigit():
        level = int(node.tag[1])
        if 1 <= level <= 6:
            return "heading", level
    if node.tag == "img":
        return "img", None
    if node.tag == "input":
        input_type = node.attrs.get("type", "text").lower()
        return {
            "checkbox": "checkbox",
            "radio": "radio",
            "button": "button",
            "submit": "button",
        }.get(input_type, "textbox"), None
    return None, None


def _name(node: Node) -> str:
    for candidate in (
        node.attrs.get("aria-label"),
        node.attrs.get("alt"),
        node.attrs.get("placeholder"),
        node.attrs.get("value") if node.tag in {"button", "input"} else None,
        node.text_content(),
    ):
        clean = " ".join(str(candidate or "").split())
        if clean:
            return clean[:2048]
    return ""


def build_accessibility_tree(
    root: Node,
    rules: tuple[Rule, ...] = (),
) -> tuple[AccessibilityNode, ...]:
    result: list[AccessibilityNode] = []

    def walk(node: Node) -> None:
        if len(result) >= MAX_ACCESSIBILITY_NODES:
            raise ValueError("accessibility_node_limit")
        if node.tag in HIDDEN_ELEMENTS:
            return
        if computed_style(node, rules).get("display", "").strip().lower() == "none":
            return
        if node.attrs.get("aria-hidden", "").strip().lower() == "true":
            return

        role, level = _role(node)
        if role:
            result.append(
                AccessibilityNode(
                    role=role,
                    name=_name(node),
                    level=level,
                    href=node.attrs.get("href") if role == "link" else None,
                    node_id=node.id,
                )
            )
        for child in node.children:
            walk(child)

    for child in root.children:
        walk(child)
    return tuple(result)
