from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1] / "mission_control" / "__init__.py"
).read_text(encoding="utf-8")


def test_bank_evidence_cli_exposes_status_register_and_append_commands():
    assert '@app.cli.command("oap-bank-evidence-status")' in SOURCE
    assert '@app.cli.command("oap-bank-evidence-register")' in SOURCE
    assert '@app.cli.command("oap-record-bank-evidence")' in SOURCE


def test_bank_evidence_append_requires_explicit_founder_confirmation():
    block = SOURCE[
        SOURCE.index('@app.cli.command("oap-record-bank-evidence")'):
        SOURCE.index('@app.cli.command("oap-market-supplier-status")')
    ]

    assert '@click.option("--yes", "yes", is_flag=True, default=False)' in block
    assert 'raise click.ClickException("explicit_confirmation_required")' in block
    assert "authority.configured_identity()" in block
    assert 'raise click.ClickException("human_authority_identity_not_configured")' in block


def test_bank_evidence_cli_uses_append_only_store_not_direct_sql():
    block = SOURCE[
        SOURCE.index('@app.cli.command("oap-record-bank-evidence")'):
        SOURCE.index('@app.cli.command("oap-market-supplier-status")')
    ]

    assert "bank_authorisation_store.record_evidence(" in block
    assert "INSERT INTO oap_bank_authorisation_evidence" not in block
    assert "UPDATE oap_bank_authorisation_evidence" not in block
    assert "DELETE FROM oap_bank_authorisation_evidence" not in block
