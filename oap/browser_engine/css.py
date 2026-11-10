"""OAP Engine CSS v1: deterministic bounded selector and cascade subset."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .dom import Node

MAX_CSS_CHARS = 512_000
MAX_CSS_RULES = 10_000
MAX_DECLARATIONS_PER_RULE = 64

ALLOWED_PROPERTIES = frozenset({
    "color",
    "background-color",
    "display",
    "font-size",
    "font-weight",
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
    "text-align",
})

_SIMPLE_SELECTOR = re.compile(
    r"^(?P<tag>\*|[A-Za-z][A-Za-z0-9_-]*)?"
    r"(?P<suffix>(?:[.#][A-Za-z0-9_-]+)*)$"
)


@dataclass(frozen=True)
class Rule:
    selector: str
    declarations: tuple[tuple[str, str], ...]
    order: int

    @property
    def specificity(self) -> tuple[int, int, int]:
        ids = classes = tags = 0
        for token in _selector_simple_tokens(self.selector):
            tag, node_id, node_classes = _parse_simple_selector(token)
            ids += 1 if node_id else 0
            classes += len(node_classes)
            tags += 1 if tag and tag != "*" else 0
        return (ids, classes, tags)


def _parse_simple_selector(
    selector: str,
) -> tuple[str | None, str | None, tuple[str, ...]]:
    match = _SIMPLE_SELECTOR.fullmatch(selector.strip())
    if match is None:
        raise ValueError("unsupported_css_selector")
    tag = match.group("tag")
    node_id: str | None = None
    classes: list[str] = []
    for prefix, value in re.findall(
        r"([.#])([A-Za-z0-9_-]+)", match.group("suffix")
    ):
        if prefix == "#":
            if node_id is not None:
                raise ValueError("multiple_selector_ids")
            node_id = value
        else:
            classes.append(value)
    return tag.lower() if tag else None, node_id, tuple(classes)


def _selector_parts(selector: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if any(token in selector for token in ("+", "~", "[", "]", ":")):
        raise ValueError("unsupported_css_selector")
    tokens = selector.replace(">", " > ").split()
    if not tokens:
        raise ValueError("empty_css_selector")

    simples: list[str] = []
    combinators: list[str] = []
    pending = " "
    expect_simple = True
    for token in tokens:
        if token == ">":
            if expect_simple or not simples:
                raise ValueError("invalid_child_selector")
            pending = ">"
            expect_simple = True
            continue
        _parse_simple_selector(token)
        if simples:
            combinators.append(pending)
        simples.append(token)
        pending = " "
        expect_simple = False
    if expect_simple:
        raise ValueError("invalid_css_selector")
    return tuple(simples), tuple(combinators)


def _selector_simple_tokens(selector: str) -> tuple[str, ...]:
    return _selector_parts(selector)[0]


def _matches_simple(node: Node, selector: str) -> bool:
    tag, node_id, classes = _parse_simple_selector(selector)
    if tag and tag != "*" and node.tag != tag:
        return False
    if node_id and node.id != node_id:
        return False
    return all(css_class in node.classes for css_class in classes)


def _matches_selector(node: Node, selector: str) -> bool:
    simples, combinators = _selector_parts(selector)
    if not _matches_simple(node, simples[-1]):
        return False

    current = node
    for index in range(len(simples) - 2, -1, -1):
        combinator = combinators[index]
        wanted = simples[index]
        if combinator == ">":
            current = current.parent
            if current is None or not _matches_simple(current, wanted):
                return False
            continue

        ancestor = current.parent
        while ancestor is not None and not _matches_simple(ancestor, wanted):
            ancestor = ancestor.parent
        if ancestor is None:
            return False
        current = ancestor
    return True


def parse_declarations(raw: str) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for index, part in enumerate(raw.split(";")):
        if index >= MAX_DECLARATIONS_PER_RULE:
            raise ValueError("css_declaration_limit")
        if ":" not in part:
            continue
        name, value = part.split(":", 1)
        name = name.strip().lower()
        value = value.strip()
        if name in ALLOWED_PROPERTIES and value:
            result.append((name, value))
    return tuple(result)


def parse_stylesheet(css: str) -> tuple[Rule, ...]:
    if len(css) > MAX_CSS_CHARS:
        raise ValueError("css_input_too_large")
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
            if not selector:
                continue
            try:
                _selector_parts(selector)
            except ValueError:
                continue
            if len(rules) >= MAX_CSS_RULES:
                raise ValueError("css_rule_limit")
            rules.append(
                Rule(
                    selector=selector,
                    declarations=declarations,
                    order=order,
                )
            )
            order += 1
    return tuple(rules)


def matches(node: Node, selector: str) -> bool:
    try:
        return _matches_selector(node, selector)
    except ValueError:
        return False


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
