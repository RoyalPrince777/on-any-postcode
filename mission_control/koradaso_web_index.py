"""KORADASO first-party, locally stored public-web index.

No third-party search provider, automatic crawling, or private user content.
A curator imports public HTTPS page metadata explicitly; queries never contact
the open web. A separate governed crawler can extend this contract later.
"""
from __future__ import annotations

import ipaddress
import os
import sqlite3
from pathlib import Path
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
            params: list[str | int] = []
            for term in terms:
                escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                clauses.append("(lower(title) LIKE ? ESCAPE '\\' OR lower(description) LIKE ? ESCAPE '\\')")
                params.extend([f"%{escaped}%", f"%{escaped}%"])
            # All terms must match; title matches rank above description-only matches.
            # Keep deterministic ordering for equally relevant public records.
            title_scores = []
            for term in terms:
                title_scores.append("(CASE WHEN lower(title) LIKE ? ESCAPE '\\\\' THEN 3 ELSE 0 END)")
                params.append(f"%{term.replace(chr(92), chr(92) * 2).replace('%', chr(92) + '%').replace('_', chr(92) + '_')}%")
            params.append(max(1, min(20, limit)))
            rows = db.execute(
                "SELECT url,title,description,indexed_at FROM public_pages WHERE "
                + " AND ".join(clauses)
                + " ORDER BY (" + " + ".join(title_scores)
                + ") DESC, indexed_at DESC, url ASC LIMIT ?",
                params,
            ).fetchall()
            return [dict(row) for row in rows if _safe_public_url(row["url"])], True
    except (sqlite3.Error, OSError):
        return [], False
