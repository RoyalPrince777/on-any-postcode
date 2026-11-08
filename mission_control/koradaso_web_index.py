"""KORADASO first-party, locally stored public-web index.

No third-party search provider, automatic crawling, or private user content.
A curator imports public HTTPS page metadata explicitly; queries never contact
the open web. A separate governed crawler can extend this contract later.
"""
from __future__ import annotations

import ipaddress
import os
import re
import sqlite3
from pathlib import Path
from textwrap import shorten
from urllib.parse import urlsplit


def _index_path() -> Path | None:
    configured = os.environ.get("OAP_KORADASO_WEB_INDEX", "").strip()
    return Path(configured).expanduser() if configured else None


def _safe_public_url(value: str) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        parts = urlsplit(value)
        host = parts.hostname or ""
        if parts.scheme != "https" or not host or parts.username or parts.password:
            return False
        if parts.port not in (None, 443) or "." not in host or any(
            c.isspace() for c in host
        ):
            return False
        if host.lower() == "localhost" or host.endswith(".localhost"):
            return False
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return "." in host and not any(c.isspace() for c in host)
        return False
    except ValueError:
        return False


def init_index(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS public_pages (
            url TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS public_pages_title ON public_pages(title)")


def ingest_public_page(path: Path, *, url: str, title: str, description: str = "") -> None:
    """Governed metadata ingestion, not an external network fetch."""
    if not _safe_public_url(url) or not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError("invalid_public_page_metadata")
    if not isinstance(description, str) or len(description) > 1200:
        raise ValueError("invalid_public_page_metadata")
    init_index(path)
    with sqlite3.connect(path) as db:
        db.execute(
            "INSERT INTO public_pages(url,title,description) VALUES(?,?,?) "
            "ON CONFLICT(url) DO UPDATE SET title=excluded.title, "
            "description=excluded.description, indexed_at=CURRENT_TIMESTAMP",
            (url, title.strip(), description.strip()),
        )


def _like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _result_snippet(description: str, terms: list[str]) -> str:
    text = " ".join(description.split())
    # Older crawls stored page chrome before the first content sentence.
    text = re.sub(r"^skip to (?:main )?content\b.*?(?:[.!?](?=\s|$)|$)", "", text,
                  count=1, flags=re.IGNORECASE).strip()
    if len(text) <= 170:
        return text
    phrase = re.escape(" ".join(terms))
    alternatives = "|".join(re.escape(term) for term in terms if len(term) > 2)
    match = re.search(rf"\b{phrase}\b", text, re.IGNORECASE)
    if match is None and alternatives:
        match = re.search(rf"\b(?:{alternatives})\b", text, re.IGNORECASE)
    if match is not None and match.start() >= 110:
        start = text.rfind(" ", 0, match.start() - 40) + 1
        if start > 0:
            text = "… " + text[start:]
    return shorten(text, width=170, placeholder="…")


def search_public_pages(query: str, *, limit: int = 20) -> tuple[list[dict[str, str]], bool]:
    """Return real indexed records, or empty and unconfigured; never simulate results."""
    path = _index_path()
    if path is None or not path.is_file():
        return [], False
    terms = [t.lower() for t in query.strip().split() if t][:8]
    if not terms or len(query) > 120:
        return [], True
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2) as db:
            db.row_factory = sqlite3.Row
            clauses = []
            patterns = [_like_pattern(term) for term in terms]
            params: list[str | int] = []
            for pattern in patterns:
                clauses.append("(lower(title) LIKE ? ESCAPE '\\' OR lower(description) LIKE ? ESCAPE '\\')")
                params.extend([pattern, pattern])
            # Prefer the full phrase in the title, then count title term matches.
            title_scores = ["(CASE WHEN lower(title) LIKE ? ESCAPE '\\' THEN 1 ELSE 0 END)"] * len(patterns)
            params.extend([_like_pattern(" ".join(terms)), *patterns])
            params.append(max(1, min(20, limit)))
            rows = db.execute(
                "SELECT url,title,description,indexed_at FROM public_pages WHERE "
                + " AND ".join(clauses)
                + " ORDER BY (lower(title) LIKE ? ESCAPE '\\') DESC, ("
                + " + ".join(title_scores)
                + ") DESC, indexed_at DESC, url ASC LIMIT ?",
                params,
            ).fetchall()
            results = []
            for row in rows:
                if _safe_public_url(row["url"]):
                    results.append(dict(row) | {
                        "domain": urlsplit(row["url"]).hostname or "",
                        "snippet": _result_snippet(row["description"], terms),
                    })
            return results, True
    except (sqlite3.Error, OSError):
        return [], False
