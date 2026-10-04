"""OAP Engine v0: bounded first-party HTML-to-display-list renderer.

This is intentionally not a standards-complete browser engine. It proves an
OAP-owned parsing/layout/render contract that can grow without misrepresenting
Android System WebView as first-party OAP technology.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from html.parser import HTMLParser

BLOCK_TAGS = {
    "article", "aside", "blockquote", "div", "footer", "form", "h1", "h2", "h3",
    "h4", "h5", "h6", "header", "li", "main", "nav", "ol", "p", "section", "ul",
}
IGNORED_TAGS = {"script", "style", "noscript", "template"}


@dataclass(frozen=True)
class DisplayItem:
    kind: str
    text: str
    x: int
    y: int
    width: int
    height: int
    href: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RenderDocument:
    title: str
    width: int
    height: int
    items: tuple[DisplayItem, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "width": self.width,
            "height": self.height,
            "items": [item.to_dict() for item in self.items],
        }


class _OapHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._title_depth = 0
        self._ignore_depth = 0
        self._href_stack: list[str | None] = []
        self.tokens: list[tuple[str, str | None, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in IGNORED_TAGS:
            self._ignore_depth += 1
            return
        if self._ignore_depth:
            return
        if tag == "title":
            self._title_depth += 1
        href = None
        if tag == "a":
            href = dict(attrs).get("href")
        self._href_stack.append(href)
        if tag in BLOCK_TAGS:
            self.tokens.append(("\n", None, True))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in IGNORED_TAGS:
            self._ignore_depth = max(0, self._ignore_depth - 1)
            return
        if self._ignore_depth:
            return
        if tag == "title":
            self._title_depth = max(0, self._title_depth - 1)
        if tag in BLOCK_TAGS:
            self.tokens.append(("\n", None, True))
        if self._href_stack:
            self._href_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._ignore_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self._title_depth:
            self.title = (self.title + " " + text).strip()
            return
        href = next((value for value in reversed(self._href_stack) if value), None)
        self.tokens.append((text, href, False))


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


def render_html(html: str, viewport_width: int = 390) -> RenderDocument:
    """Render a safe text-first subset of HTML to an OAP display list.

    v0 deliberately implements no CSS cascade, JavaScript, forms, media,
    networking, cookies, storage, accessibility tree, or compositing.
    """
    if viewport_width < 160:
        raise ValueError("viewport_width must be at least 160")

    parser = _OapHtmlParser()
    parser.feed(html)
    parser.close()

    margin = 16
    line_height = 24
    char_width = 8
    content_width = max(1, viewport_width - (margin * 2))
    max_chars = max(1, content_width // char_width)
    y = margin
    items: list[DisplayItem] = []

    pending_break = False
    for text, href, is_break in parser.tokens:
        if is_break:
            pending_break = True
            continue
        if pending_break and items:
            y += 8
        pending_break = False
        for line in _wrap_words(text, max_chars):
            items.append(
                DisplayItem(
                    kind="link" if href else "text",
                    text=line,
                    x=margin,
                    y=y,
                    width=min(content_width, len(line) * char_width),
                    height=line_height,
                    href=href,
                )
            )
            y += line_height

    return RenderDocument(
        title=parser.title or "Untitled",
        width=viewport_width,
        height=max(y + margin, line_height + margin * 2),
        items=tuple(items),
    )
