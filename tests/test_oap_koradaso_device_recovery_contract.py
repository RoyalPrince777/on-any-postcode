from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/oap_koradaso_device_recovery.sh").read_text()


def test_device_recovery_preserves_work_and_is_idempotent():
    assert 'route_tag = \'@app.get("/koradaso")\'' in SCRIPT
    assert 'source.count(marker) != 1' in SCRIPT
    assert 'compile(updated, str(app_path), "exec")' in SCRIPT
    assert 'shutil.copy2(app_path, backup)' in SCRIPT
    assert 'os.replace(tmp, app_path)' in SCRIPT
    assert 'template.open("xb")' in SCRIPT
    assert 'if route_missing:' in SCRIPT
    assert "git reset" not in SCRIPT
    assert "git clean" not in SCRIPT
    assert "git switch" not in SCRIPT
    assert "pip install" not in SCRIPT


def test_device_recovery_checks_public_and_private_routes_without_approval_bypass():
    assert 'expected_public = ("/world", "/koradaso")' in SCRIPT
    assert 'res.status_code != 200' in SCRIPT
    assert 'res.status_code not in (302, 303, 401, 403, 503)' in SCRIPT
    assert "OAP_AUTH_REQUIRED=true" in SCRIPT
    assert "OAP_KORADASO_DEVICE_ROUTE_PROOF_PASSED" in SCRIPT
    assert "app.run(" not in SCRIPT
    assert "OAP_SMI_GATEWAY_SECRET" not in SCRIPT
