"""Read-only readiness evidence for an OAP OS Generation 0 Android Home Node.

Does not start workers, source credentials, read private files, acquire GPS,
install software, modify Android, contact a server, or certify a physical phone.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path


def _revision(repo: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"],
            capture_output=True, text=True, timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and len(value) == 40 and all(
        c in "0123456789abcdef" for c in value.lower()
    ) else None


def readiness(*, home: Path | None = None, repo: Path | None = None,
              android_host: bool | None = None) -> dict[str, object]:
    home = home or Path.home()
    repo = repo or Path(os.environ.get("OAP_HOME_REPO", str(home / "on-any-postcode")))
    if android_host is None:
        android_host = bool(os.environ.get("ANDROID_ROOT")) and (
            "com.termux" in os.environ.get("PREFIX", "")
        )
    revision = _revision(repo) if (repo / ".git").is_dir() else None
    return {
        "component": "OAP OS Android Home Node readiness",
        "generation": 0,
        "host": "android_termux" if android_host else "other_or_unverified",
        "physical_device_verified": False,
        "custom_android_os": False,
        "native_apk": False,
        "repository_revision": revision,
        "repo_present": (repo / ".git").is_dir(),
        "worker_runner_present": (repo / "scripts/termux_home_node_run.sh").is_file(),
        "map_runtime_bridge_present": (
            repo / "mission_control/static/oap_os_map_bridge.js"
        ).is_file(),
        "private_env_present": (
            home / ".config/oap/home-node.env"
        ).is_file(),
        "device_location_permission": "not_checked",
        "map_road_source": "not_checked",
        "production_mapping": "not_checked",
        "ready_for_device_certification": False,
        "read_only": True,
    }


if __name__ == "__main__":
    print(json.dumps(readiness(), sort_keys=True))
