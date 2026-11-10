"""Bounded in-memory response cache foundation for OAP Engine."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from .origin import parse_origin

MAX_CACHE_ENTRIES = 128
MAX_CACHE_ENTRY_BYTES = 512 * 1024
DEFAULT_CACHE_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class CacheEntry:
    url: str
    content_type: str
    body: bytes


class ResponseCache:
    def __init__(self, *, max_bytes: int = DEFAULT_CACHE_BYTES) -> None:
        if max_bytes < MAX_CACHE_ENTRY_BYTES:
            raise ValueError("cache_max_bytes_too_small")
        self._max_bytes = int(max_bytes)
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._size = 0

    @staticmethod
    def _key(url: object) -> str:
        raw = str(url or "").strip()
        parse_origin(raw)
        return raw

    def put(self, url: object, body: bytes, *, content_type: str) -> None:
        key = self._key(url)
        payload = bytes(body)
        if len(payload) > MAX_CACHE_ENTRY_BYTES:
            raise ValueError("cache_entry_too_large")
        previous = self._entries.pop(key, None)
        if previous is not None:
            self._size -= len(previous.body)
        entry = CacheEntry(key, str(content_type or "")[:256], payload)
        self._entries[key] = entry
        self._size += len(payload)
        while self._size > self._max_bytes or len(self._entries) > MAX_CACHE_ENTRIES:
            _, evicted = self._entries.popitem(last=False)
            self._size -= len(evicted.body)

    def get(self, url: object) -> CacheEntry | None:
        key = self._key(url)
        entry = self._entries.pop(key, None)
        if entry is None:
            return None
        self._entries[key] = entry
        return entry

    def clear(self) -> None:
        self._entries.clear()
        self._size = 0

    @property
    def size_bytes(self) -> int:
        return self._size
