"""Offline regression checks for local backup safety and Git history custody."""
from pathlib import Path
import os
import shutil
import sqlite3
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "backup.sh"


@pytest.mark.skipif(not shutil.which("git") or not shutil.which("bash"), reason="requires git and bash")
def test_local_backup_contains_valid_sqlite_and_git_bundle(tmp_path):
    root = tmp_path / "oap"
    root.mkdir()
    (root / "app.py").write_text("print('OAP')\n")
    db = sqlite3.connect(root / "oap.db")
    db.execute("CREATE TABLE proof (value TEXT)")
    db.execute("INSERT INTO proof VALUES ('present')")
    db.commit()
    db.close()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "app.py"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=OAP Test",
         "-c", "user.email=test@example.invalid", "commit", "-qm", "initial"],
        check=True,
    )
    env = {**os.environ, "OAP_BACKUP_ROOT": str(root)}
    result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    snapshots = list((root / "backups").glob("oap-*"))
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    with sqlite3.connect(snapshot / "oap.db") as restored:
        assert restored.execute("SELECT value FROM proof").fetchone() == ("present",)
    subprocess.run(["git", "-C", str(root), "bundle", "verify",
                    str(snapshot / "oap-history.bundle")], check=True, capture_output=True)
    assert (snapshot / "SHA256SUMS").exists()
    # Verify actual independent clone, not only bundle metadata.
    recovered = tmp_path / "recovered"
    subprocess.run(["git", "clone", "-q", str(snapshot / "oap-history.bundle"),
                    str(recovered)], check=True)
    assert (recovered / "app.py").read_text() == (root / "app.py").read_text()
    original_head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    recovered_head = subprocess.check_output(
        ["git", "-C", str(recovered), "rev-parse", "HEAD"], text=True
    ).strip()
    assert recovered_head == original_head


@pytest.mark.skipif(not shutil.which("bash"), reason="requires bash")
def test_local_backup_fails_without_source_and_does_not_claim_success(tmp_path):
    root = tmp_path / "oap"
    root.mkdir()
    env = {**os.environ, "OAP_BACKUP_ROOT": str(root)}
    result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Local backup complete" not in result.stdout
