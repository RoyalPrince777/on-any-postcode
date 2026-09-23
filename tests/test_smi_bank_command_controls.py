"""The SMI bank menu is a non-operational Founder review surface."""
from pathlib import Path

JS = Path(__file__).resolve().parents[1] / "mission_control/static/smi_command_centre.js"
CSS = Path(__file__).resolve().parents[1] / "mission_control/static/smi_command_centre.css"


def test_bank_control_uses_existing_smi_command_centre() -> None:
    script = JS.read_text(encoding="utf-8")
    assert '["🏦 Bank Controls","oap-bank-controls"]' in script
    assert 'bankControls.hidden=!bankControls.hidden' in script
    assert 'action==="oap-bank-controls"' in script
    assert 'bankControls.setAttribute("aria-label","USA Royalty Bank Founder controls · review only")' in script
    assert 'universe.after(bankControls)' in script


def test_all_bank_review_controls_are_non_operational() -> None:
    script = JS.read_text(encoding="utf-8")
    for label in ("Mind", "Body", "Soul", "Post Office", "OAP Store", "Founder Final"):
        assert f'["' in script and label in script
    for invariant in (
        "SIKA Recognition is not GBP or issued SIKA",
        "Cash-in, cash-out and physical service locations are not verified or activated",
        "Supplied package checklist fields do not constitute independently verified artifact proof",
        "No action here authorises transfers",
    ):
        assert invariant in script
    assert ".smi-command-bank-controls[hidden]{display:none!important}" in CSS.read_text(encoding="utf-8")
