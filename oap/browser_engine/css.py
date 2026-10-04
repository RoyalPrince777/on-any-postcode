"""OAP Engine CSS v0: deterministic selector and cascade subset."""
from __future__ import annotations

from dataclasses import dataclass

from .dom import Node

ALLOWED_PROPERTIES = frozenset({
    "color",
    "background-color",
    "display",
    "font-size",
    "font-weight",
    "margin",
    "padding",
    "text-align",
})


@dataclass(frozen=True)
class Rule:
    selector: str
    declarations: tuple[tuple[str, str], ...]
    order: int

    @property
    def specificity(self) -> tuple[int, int, int]:
        selector = self.selector.strip()
        if selector.startswith("#"):
            return (1, 0, 0)
        if selector.startswith("."):
            return (0, 1, 0)
        return (0, 0, 1)


def parse_declarations(raw: str) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for part in raw.split(";"):
        if ":" not in part:
            continue
        name, value = part.split(":", 1)
        name = name.strip().lower()
        value = value.strip()
        if name in ALLOWED_PROPERTIES and value:
            result.append((name, value))
    return tuple(result)


def parse_stylesheet(css: str) -> tuple[Rule, ...]:
    rules: list[Rule] = []
    order = 0
    for chunk in css.split("}"):
        if "{" not in chunk:
            continue
        selectors, raw_declarations = chunk.split("{", 1)
        declarations = parse_declarations(raw_declarations)
        if not declarations:
            continue
        for selector in selectors.split(","):
            selector = selector.strip()
            if not selector or any(token in selector for token in (" ", ">", "+", "~", "[", ":")):
                continue
            rules.append(Rule(selector=selector, declarations=declarations, order=order))
            order += 1
    return tuple(rules)


def matches(node: Node, selector: str) -> bool:
    if selector.startswith("#"):
        return node.id == selector[1:]
    if selector.startswith("."):
        return selector[1:] in node.classes
    return node.tag == selector.lower()


def computed_style(node: Node, rules: tuple[Rule, ...]) -> dict[str, str]:
    winners: dict[str, tuple[tuple[int, int, int], int, str]] = {}
    for rule in rules:
        if not matches(node, rule.selector):
            continue
        for name, value in rule.declarations:
            candidate = (rule.specificity, rule.order, value)
            current = winners.get(name)
            if current is None or candidate[:2] >= current[:2]:
                winners[name] = candidate

    inline = parse_declarations(node.attrs.get("style", ""))
    for name, value in inline:
        winners[name] = ((2, 0, 0), 10**9, value)

    return {name: winner[2] for name, winner in winners.items()}
