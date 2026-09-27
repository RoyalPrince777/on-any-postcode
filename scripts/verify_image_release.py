#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request

MANIFEST = os.path.join(os.path.dirname(__file__), "..", "deploy", "render-image-release.json")

def check(name, cfg):
    url = cfg["public_url"].rstrip("/") + cfg["health_path"]
    req = urllib.request.Request(url, headers={"User-Agent": "OAP-release-verifier/1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read(4096).decode('utf-8', 'replace')
            ok = 200 <= response.status < 300
            print(f"{name}: status={response.status} ok={ok} url={url} body={body[:200]!r}")
            return ok
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"{name}: ok=False url={url} error={exc}", file=sys.stderr)
        return False

def main():
    with open(MANIFEST, 'r', encoding='utf-8') as fh:
        manifest = json.load(fh)
    image = manifest["image"]["immutable_ref"]
    print("release_commit=" + manifest["release_commit"])
    print("immutable_image=" + image)
    results = [check(name, cfg) for name, cfg in manifest["services"].items()]
    raise SystemExit(0 if all(results) else 1)

if __name__ == "__main__":
    main()
