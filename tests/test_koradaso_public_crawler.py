"""Security and integration tests for manual KORADASO public crawler.

No network connection is made: transports and robots policies are patched.
"""
import ipaddress
import socket

import pytest

from mission_control import koradaso_public_crawler as crawler
from mission_control.koradaso_web_index import search_public_pages


def test_private_and_local_addresses_fail_before_network():
    for target in (
        "http://example.org/", "https://127.0.0.1/", "https://10.0.0.3/",
        "https://169.254.169.254/", "https://localhost/",
        "https://example.org:4443/", "https://u:p@example.org/",
    ):
        with pytest.raises(crawler.CrawlDenied):
            crawler._target(target)


def test_dns_mixed_public_and_private_is_denied(monkeypatch):
    def fake_dns(*_args, **_kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]
    monkeypatch.setattr(crawler.socket, "getaddrinfo", fake_dns)
    with pytest.raises(crawler.CrawlDenied, match="non_public_dns_destination"):
        crawler._public_ips("example.org")


def test_public_ip_resolution_only(monkeypatch):
    def fake_dns(*_args, **_kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]
    monkeypatch.setattr(crawler.socket, "getaddrinfo", fake_dns)
    assert crawler._public_ips("example.org") == ("8.8.8.8",)


def test_single_origin_robots_noindex_and_real_index(monkeypatch, tmp_path):
    class Robots:
        def can_fetch(self, _ua, url):
            return not url.endswith("/blocked")

    pages = {
        "https://example.org/": b'<html><head><title>Public KORADASO directory</title><meta name="description" content="Genuine public documents"></head><body><a href="/article">Article</a><a href="/blocked">Blocked</a><a href="https://outside.org/">External</a></body></html>',
        "https://example.org/article": b'<html><head><title>Oware public article</title></head></html>',
    }

    monkeypatch.setattr(crawler, "_robots", lambda _host: Robots())

    def fake_fetch(url, **_kwargs):
        assert url in pages
        return "text/html", pages[url]

    monkeypatch.setattr(crawler, "_fetch", fake_fetch)
    db = tmp_path / "web.sqlite"
    result = crawler.crawl_public_seed("https://example.org/", db, sleep_seconds=0)
    assert result["indexed"] == 2
    assert result["skipped"] == 1
    assert result["scope"] == "one_public_https_host"
    monkeypatch.setenv("OAP_KORADASO_WEB_INDEX", str(db))
    matches, ready = search_public_pages("oware")
    assert ready and len(matches) == 1
    assert matches[0]["url"] == "https://example.org/article"


def test_noindex_is_not_imported(monkeypatch, tmp_path):
    class Robots:
        def can_fetch(self, _ua, _url):
            return True
    monkeypatch.setattr(crawler, "_robots", lambda _host: Robots())
    monkeypatch.setattr(crawler, "_fetch", lambda _url, **_kw: (
        "text/html", b'<html><head><title>Hidden</title><meta name="robots" content="noindex"></head></html>'
    ))
    result = crawler.crawl_public_seed("https://example.org/", tmp_path / "index.sqlite", sleep_seconds=0)
    assert result["indexed"] == 0
    assert result["skipped"] == 1


def test_robots_unavailable_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, "_fetch", lambda *_args, **_kwargs: (
        "text/html", b"<html><title>robots unavailable</title></html>"
    ))
    # Empty robots policy is allowed by robotparser; test explicit fetch failure instead.
    def denied(*_args, **_kwargs):
        raise crawler.CrawlDenied("http_status_not_200")
    monkeypatch.setattr(crawler, "_fetch", denied)
    with pytest.raises(crawler.CrawlDenied, match="robots_unavailable_or_denied"):
        crawler.crawl_public_seed("https://example.org/", tmp_path / "index.sqlite")
