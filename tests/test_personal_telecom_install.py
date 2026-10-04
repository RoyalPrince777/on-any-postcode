from pathlib import Path

import pytest

from mission_control import infrastructure, personal_telecom_install


def test_personal_telecom_installer_preflight_is_software_ready(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_PERSONAL_TELECOM_HOME", str(tmp_path))
    for env_name in personal_telecom_install.REFERENCE_ENV.values():
        monkeypatch.delenv(env_name, raising=False)

    result = personal_telecom_install.preflight()

    assert result["software_contract_valid"] is True
    assert result["ready_to_install_software"] is True
    assert result["external_activation_ready"] is False
    assert result["external_execution_enabled"] is False
    assert result["sensitive_material_exposed"] is False


def test_personal_telecom_installer_requires_human_approval(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_PERSONAL_TELECOM_HOME", str(tmp_path))

    with pytest.raises(RuntimeError):
        personal_telecom_install.install()


def test_dry_run_never_writes_install_state(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_PERSONAL_TELECOM_HOME", str(tmp_path))

    result = personal_telecom_install.install(assume_yes=True, dry_run=True)

    assert result["installed"] is False
    assert not (tmp_path / personal_telecom_install.MANIFEST_NAME).exists()
    assert result["external_execution_changed"] is False


def test_apply_writes_private_non_operational_manifest(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_PERSONAL_TELECOM_HOME", str(tmp_path))

    result = personal_telecom_install.install(assume_yes=True, dry_run=False)
    manifest = tmp_path / personal_telecom_install.MANIFEST_NAME

    assert result["installed"] is True
    assert manifest.is_file()
    assert manifest.stat().st_mode & 0o777 == 0o600
    text = manifest.read_text(encoding="utf-8")
    assert '"oap_number": "OAP-25-8-000001"' in text
    assert '"real_carrier_profile_installed": false' in text
    assert '"private_radio_transmission_enabled": false' in text


def test_authority_references_are_opaque_and_not_returned(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_PERSONAL_TELECOM_HOME", str(tmp_path))
    monkeypatch.setenv("OAP_PRIVATE_RADIO_AUTHORITY_REF", "licence-reference-private")

    refs = personal_telecom_install.authority_references()

    assert refs["private_radio"]["configured"] is True
    assert refs["private_radio"]["reference_exposed"] is False
    assert "licence-reference-private" not in repr(refs)


def test_all_authority_references_only_change_external_activation_readiness(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_PERSONAL_TELECOM_HOME", str(tmp_path))
    for env_name in personal_telecom_install.REFERENCE_ENV.values():
        monkeypatch.setenv(env_name, f"configured-{env_name.lower()}")

    preflight = personal_telecom_install.preflight()
    install = personal_telecom_install.install(assume_yes=True, dry_run=False)

    assert preflight["external_activation_ready"] is True
    assert preflight["external_execution_enabled"] is False
    assert install["external_activation_ready"] is True
    assert install["external_execution_changed"] is False


def test_uninstall_preserves_oap_number_and_does_not_change_external_execution(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_PERSONAL_TELECOM_HOME", str(tmp_path))
    personal_telecom_install.install(assume_yes=True, dry_run=False)

    result = personal_telecom_install.uninstall(assume_yes=True, dry_run=False)

    assert result["removed"] is True
    assert result["oap_number_preserved"] is True
    assert result["external_execution_changed"] is False


def test_infrastructure_exposes_install_readiness_without_activation(monkeypatch, tmp_path):
    monkeypatch.setenv("OAP_PERSONAL_TELECOM_HOME", str(tmp_path))

    projection = infrastructure.get_public_infrastructure()
    install = projection["personal_telecom_install"]

    assert install["installer_built"] is True
    assert install["software_ready"] is True
    assert install["external_execution_enabled"] is False
    assert install["human_authority_final"] is True
