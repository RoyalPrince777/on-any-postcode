"""Quota-bounded, per-origin OAP Engine storage foundation.

This is an in-process storage primitive, not durable browser storage yet.
"""
from __future__ import annotations

from collections import defaultdict

from .origin import Origin, parse_origin

DEFAULT_ORIGIN_QUOTA_BYTES = 64 * 1024
MAX_KEYS_PER_ORIGIN = 256
MAX_KEY_BYTES = 256
MAX_VALUE_BYTES = 16 * 1024


class OriginStorage:
    def __init__(self, *, quota_bytes: int = DEFAULT_ORIGIN_QUOTA_BYTES) -> None:
        if quota_bytes < 1024:
            raise ValueError("quota_bytes_too_small")
        self._quota_bytes = int(quota_bytes)
        self._data: dict[Origin, dict[str, str]] = defaultdict(dict)

    @staticmethod
    def _bytes(value: str) -> int:
        return len(value.encode("utf-8"))

    def _origin(self, url: object) -> Origin:
        return parse_origin(url)

    def get_item(self, url: object, key: object) -> str | None:
        origin = self._origin(url)
        return self._data.get(origin, {}).get(str(key))

    def set_item(self, url: object, key: object, value: object) -> None:
        origin = self._origin(url)
        clean_key = str(key)
        clean_value = str(value)
        if not clean_key or self._bytes(clean_key) > MAX_KEY_BYTES:
            raise ValueError("invalid_storage_key")
        if self._bytes(clean_value) > MAX_VALUE_BYTES:
            raise ValueError("storage_value_too_large")

        bucket = self._data[origin]
        if clean_key not in bucket and len(bucket) >= MAX_KEYS_PER_ORIGIN:
            raise ValueError("storage_key_limit")

        candidate = dict(bucket)
        candidate[clean_key] = clean_value
        usage = sum(self._bytes(k) + self._bytes(v) for k, v in candidate.items())
        if usage > self._quota_bytes:
            raise ValueError("origin_storage_quota_exceeded")
        bucket[clean_key] = clean_value

    def remove_item(self, url: object, key: object) -> None:
        origin = self._origin(url)
        bucket = self._data.get(origin)
        if bucket is not None:
            bucket.pop(str(key), None)
            if not bucket:
                self._data.pop(origin, None)

    def clear_origin(self, url: object) -> None:
        self._data.pop(self._origin(url), None)

    def usage_bytes(self, url: object) -> int:
        bucket = self._data.get(self._origin(url), {})
        return sum(self._bytes(k) + self._bytes(v) for k, v in bucket.items())

    def snapshot(self, url: object) -> dict[str, str]:
        return dict(self._data.get(self._origin(url), {}))
