"""No live network use: verify safe crawler contracts with controlled response stubs."""
from pathlib import Path

import pytest

from mission_control import koradaso_crawler
from mission_control.koradaso_web_index import search_public_pages


def test_public_seed_crawl_indexes_real_html_when_robots_allow(tmp_path, monkeypatch):
    db = tmp_path / "pages.sqlite3"
    monkeypatch.setenv("OAP_KORADASO_WEB_INDEX", str(db))
    requested = []

    def fetch(host, target, *, limit):
        requested.append((host, target, limit))
        if target == "/robots.txt":
            return 200, "text/plain; charset=utf-8", b"User-agent: *\\nAllow: /\\n"
        return (
            200, "text/html; charset=utf-8",
            b"<html><head><title>Oware club</title>"
            b'<meta name="description" content="A real local gathering">'
            b"</head><body><script>private data</script>Public club</body></html>",
        )

    monkeypatch.setattr(koradaso_crawler, "_fetch", fetch)
    record = koradaso_crawler.crawl_seed("https://example.org/oware", db)
    assert record["title"] == "Oware club"
    assert record["description"] == "A real local gathering"
    assert requested == [
        ("example.org", "/robots.txt", koradaso_crawler.MAX_ROBOTS),
        ("example.org", "/oware", koradaso_crawler.MAX_HTML),
    ]
    results, configured = search_public_pages("oware")
    assert configured is True
    assert [result["title"] for result in results] == ["Oware club"]


def test_robots_disallow_prevents_page_fetch_and_index(tmp_path, monkeypatch):
    requested = []

    def fetch(host, target, *, limit):
        requested.append(target)
        return 200, "text/plain", b"User-agent: *\\nDisallow: /private\\n"

    monkeypatch.setattr(koradaso_crawler, "_fetch", fetch)
    db = tmp_path / "pages.sqlite3"
    with pytest.raises(koradaso_crawler.CrawlerRejected, match="robots_disallow"):
        koradaso_crawler.crawl_seed("https://example.org/private", db)
    assert requested == ["/robots.txt"]
    assert not db.exists()


def test_unavailable_robots_and_redirect_never_crawl_target(tmp_path, monkeypatch):
    seen = []

    def fetch(host, target, *, limit):
        seen.append(target)
        return 302, "text/html", b""

    monkeypatch.setattr(koradaso_crawler, "_fetch", fetch)
    with pytest.raises(koradaso_crawler.CrawlerRejected, match="robots_policy_unavailable"):
        koradaso_crawler.crawl_seed("https://example.org/announcement", tmp_path / "db")
    assert seen == ["/robots.txt"]


@pytest.mark.parametrize("url", [
    "http://example.org/", "https://127.0.0.1/private",
    "https://localhost/admin", "https://user:secret@example.org/",
    "https://example.org/page#fragment",
])
def test_unsafe_seeds_fail_before_fetch(tmp_path, monkeypatch, url):
    def no_fetch(*args, **kwargs):
        pytest.fail("unsafe seed reached network")
    monkeypatch.setattr(koradaso_crawler, "_fetch", no_fetch)
    with pytest.raises(koradaso_crawler.CrawlerRejected):
        koradaso_crawler.crawl_seed(url, tmp_path / "db")


def test_dns_rejects_any_private_answer_and_no_dns(monkeypatch):
    def mixed(host, port, *, type):
        return [
            (2, 1, 6, "", ("8.8.8.8", 443)),
            (2, 1, 6, "", ("127.0.0.1", 443)),
        ]
    monkeypatch.setattr(koradaso_crawler.socket, "getaddrinfo", mixed)
    with pytest.raises(koradaso_crawler.CrawlerRejected, match="non_public_dns_destination"):
        koradaso_crawler._public_addresses("example.org")


def test_oversized_page_is_not_indexed(tmp_path, monkeypatch):
    def fetch(host, target, *, limit):
        if target == "/robots.txt":
            return 200, "text/plain", b"User-agent: *\\nAllow: /\\n"
        raise koradaso_crawler.CrawlerRejected("response_too_large")
    monkeypatch.setattr(koradaso_crawler, "_fetch", fetch)
    db = tmp_path / "db"
    with pytest.raises(koradaso_crawler.CrawlerRejected, match="response_too_large"):
        koradaso_crawler.crawl_seed("https://example.org/", db)
    assert not db.exists()


def test_runner_requires_explicit_execute():
    script = Path("scripts/koradaso_crawl_seeds.py").read_text(encoding="utf-8")
    assert 'parser.add_argument("--execute", action="store_true"' in script
    assert "if not args.execute:" in script
    assert "len(urls) > 10" in script
    assert "time.sleep(2)" in script
