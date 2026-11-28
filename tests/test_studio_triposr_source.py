"""Verify pinned upstream source bytes and syntax without importing model code."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "third_party" / "triposr"


def test_triposr_source_provenance_and_syntax():
    manifest = json.loads((ROOT / "UPSTREAM.json").read_text())
    assert manifest["execution_granted"] is False
    assert manifest["weights"]["installed"] is False
    assert manifest["runtime_verified"] is False
    for item in manifest["files"]:
        raw = (ROOT / item["path"]).read_bytes()
        blob = b"blob " + str(len(raw)).encode() + b"\0" + raw
        assert hashlib.sha1(blob, usedforsecurity=False).hexdigest() == item["upstream_git_blob_sha"]
        if item["path"].endswith(".py"):
            ast.parse(raw, filename=item["path"])
    assert (ROOT / "run.py").is_file()
    assert (ROOT / "tsr" / "system.py").is_file()
