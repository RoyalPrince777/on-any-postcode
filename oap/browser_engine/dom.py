"""OAP Engine DOM v0: bounded first-party document tree."""
from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}
HIDDEN_ELEMENTS = {"script", "style", "template", "noscript"}
MAX_HTML_CHARS = 2_000_000
MAX_DOM_NODES = 50_000
MAX_DOM_DEPTH = 512


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    text: str = ""
    children: list[Node] = field(default_factory=list)
    parent: Node | None = field(default=None, repr=False)

    @property
    def id(self) -> str | None:
        return self.attrs.get("id") or None

    @property
    def classes(self) -> frozenset[str]:
        return frozenset(self.attrs.get("class", "").split())

    def append(self, child: Node) -> None:
        child.parent = self
        self.children.append(child)

    def descendants(self) -> list[Node]:
        result: list[Node] = []
        for child in self.children:
            result.append(child)
            result.extend(child.descendants())
        return result

    def text_content(self) -> str:
        parts = [self.text] if self.text else []
        for child in self.children:
            if child.tag not in HIDDEN_ELEMENTS:
                value = child.text_content()
                if value:
                    parts.append(value)
        return " ".join(" ".join(parts).split())


class _DomParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.node_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.node_count += 1
        if self.node_count > MAX_DOM_NODES:
            raise ValueError("dom_node_limit")
        if len(self.stack) > MAX_DOM_DEPTH:
            raise ValueError("dom_depth_limit")
        clean = {name.lower(): value or "" for name, value in attrs}
        node = Node(tag.lower(), attrs=clean)
        self.stack[-1].append(node)
        if node.tag not in VOID_ELEMENTS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        target = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == target:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            current = self.stack[-1]
            current.text = " ".join(part for part in (current.text, value) if part)


def parse_html_document(html: str) -> Node:
    if len(html) > MAX_HTML_CHARS:
        raise ValueError("html_input_too_large")
    parser = _DomParser()
    parser.feed(html)
    parser.close()
    return parser.root
