"""Bounded first-party OAP TV byte-range parser.

Pure transport primitive only: NO access authorization, rights approval, storage,
publication, playback enablement, or network side effects. The caller MUST
authenticate the viewer, verify owner scope and rights/entitlement, and resolve
a trusted server-side asset before using a returned range.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_RANGE = re.compile(r"^bytes=(\d*)-(\d*)$", re.ASCII)


@dataclass(frozen=True)
class ByteRange:
    start: int
    end: int
    total: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    @property
    def content_range(self) -> str:
        return f"bytes {self.start}-{self.end}/{self.total}"


class UnsatisfiableRange(ValueError):
    """Invalid, unsupported or unsatisfiable single byte range."""


def parse_single_range(header: str, total: int) -> ByteRange:
    """Parse one RFC 7233-style bytes range; fail closed for malformed inputs.

    A caller may respond 416 with Content-Range: bytes */<total>.
    Multiple ranges are intentionally unsupported to bound resource use.
    """
    if not isinstance(total, int) or isinstance(total, bool) or total <= 0:
        raise UnsatisfiableRange("empty or invalid resource")
    if not isinstance(header, str) or len(header) > 128:
        raise UnsatisfiableRange("invalid header")
    match = _RANGE.fullmatch(header)
    if match is None:
        raise UnsatisfiableRange("single bytes range required")
    first, last = match.groups()
    if not first and not last:
        raise UnsatisfiableRange("missing bounds")
    if first:
        start = int(first)
        end = min(int(last), total - 1) if last else total - 1
        if start >= total or end < start:
            raise UnsatisfiableRange("range not satisfiable")
    else:
        suffix = int(last)
        if suffix <= 0:
            raise UnsatisfiableRange("invalid suffix")
        start, end = max(total - suffix, 0), total - 1
    return ByteRange(start, end, total)
