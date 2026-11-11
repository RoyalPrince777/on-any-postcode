"""Local SIKA 5052 upgrade recovery must stay idempotent and fail closed."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apply_sika_5052.py"
SPEC = spec_from_file_location("sika_5052_local_repair", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
repair = module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


def test_current_integrated_source_is_idempotent():
    root = Path(__file__).resolve().parents[1]
    for relative, transform in repair.FILES.items():
        current = (root / relative).read_text(encoding="utf-8")
        assert repair.TRANSFORMS[transform](current) == current


def test_missing_anchor_fails_closed():
    with pytest.raises(ValueError):
        repair.apply_store("from . import other_modules\n")
    with pytest.raises(ValueError):
        repair.apply_bank_html("<html>not an OAP bank page</html>")


def test_legacy_bank_page_removes_unverified_install_button():
    old = """{% set oap_app_name = 'OAP Bank' %}
<header class="top"><div class="brand">👑 OAP BANK</div><a class="pill" href="/pay">OAP Pay</a></header>
<div class="install-row">
<button class="pill" type="button" data-oap-install hidden>Install OAP Bank</button>
<div class="meta" data-oap-install-status role="status">Checking install support</div>
</div>
<a class="nav" href="/pay/bank/accounts"><strong>▤</strong>Accounts</a>"""
    upgraded = repair.apply_bank_html(old)
    assert "Install OAP Bank" not in upgraded
    assert "Browser access available" in upgraded
    assert "{% set oap_install_script = false %}" in upgraded
    assert 'href="/pay/bank/me"' in upgraded
    assert repair.apply_bank_html(upgraded) == upgraded
