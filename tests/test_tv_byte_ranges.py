"""Regression tests for the isolated OAP TV byte-range transport primitive."""
import pytest

from mission_control.tv_byte_ranges import UnsatisfiableRange, parse_single_range


@pytest.mark.parametrize(("header", "expected"), [
    ("bytes=0-9", (0, 9, 10)),
    ("bytes=10-", (10, 99, 90)),
    ("bytes=-5", (95, 99, 5)),
    ("bytes=0-999", (0, 99, 100)),
    ("bytes=-999", (0, 99, 100)),
])
def test_single_range(header, expected):
    result = parse_single_range(header, 100)
    assert (result.start, result.end, result.length) == expected
    assert result.content_range == f"bytes {result.start}-{result.end}/100"


@pytest.mark.parametrize("header", [
    "", "bytes=", "bytes=-", "bytes=100-", "bytes=9-3",
    "bytes=-0", "bytes=0-1,3-4", "items=0-1", "bytes= 0-1",
    "bytes=+1-2", "bytes=0-1\r\nInjected: yes", "bytes=0-1 ",
])
def test_invalid_ranges_fail_closed(header):
    with pytest.raises(UnsatisfiableRange):
        parse_single_range(header, 100)


@pytest.mark.parametrize("total", [0, -1, True, None])
def test_invalid_resource_fails_closed(total):
    with pytest.raises(UnsatisfiableRange):
        parse_single_range("bytes=0-", total)


def test_no_access_or_publication_authority():
    from pathlib import Path
    source = Path("mission_control/tv_byte_ranges.py").read_text()
    for forbidden in ("@app.", "Blueprint(", "send_file(", "INSERT INTO",
                      "rights_verified = True", "playback_enabled = True"):
        assert forbidden not in source
