from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", "node_modules"}
TEXT_SUFFIXES = {".py", ".js", ".cjs", ".mjs", ".ts", ".tsx", ".json", ".yml", ".yaml", ".md", ".txt", ".env", ".toml"}

PATTERNS = {
    "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai_live_key_shape": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "aws_access_key_shape": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_pat_shape": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
}

ALLOWLIST_MARKERS = (
    "example",
    "placeholder",
    "dummy",
    "test-only",
    "test_only",
    "fake-",
    "fake_",
)

def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != ".env":
            continue
        yield path

def main() -> int:
    findings = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.end())
                if line_end < 0:
                    line_end = len(text)
                line = text[line_start:line_end]
                if any(marker in line.lower() for marker in ALLOWLIST_MARKERS):
                    continue
                line_no = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(ROOT)}:{line_no}:{name}")
    if findings:
        print("OAP_SECRET_SCAN_FAIL")
        for finding in findings:
            print(finding)
        return 1
    print("OAP_SECRET_SCAN_PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
