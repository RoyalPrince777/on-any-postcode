VIEWS = "mission_control/planetary_domains_views.py"
TEMPLATE = "mission_control/templates/planetary_domains.html"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_planetary_ui_exposes_dedicated_cyber_and_fusion_dashboards():
    source = _read(VIEWS)
    assert '@bp.get("/cyber")' in source
    assert "def cyber_dashboard()" in source
    assert '@bp.get("/smi-fusion")' in source
    assert "def smi_fusion_dashboard()" in source


def test_planetary_ui_keeps_all_seven_domain_navigation_entries_dynamic():
    template = _read(TEMPLATE)
    assert 'aria-label="Planetary dashboard navigation"' in template
    assert "{% for domain in planetary.operational_domains %}" in template
    assert "planetary_domains.domain_dashboard" in template


def test_planetary_ui_has_accessibility_and_mobile_boundaries():
    template = _read(TEMPLATE)
    assert 'class="skip"' in template
    assert "prefers-reduced-motion" in template
    assert "@media(max-width:680px)" in template


def test_planetary_ui_preserves_truth_and_human_authority_boundary():
    template = _read(TEMPLATE)
    assert "Truth boundary:" in template
    assert "Universal live runtime remains evidence-gated" in template
    assert "Human Final Authority" in template
