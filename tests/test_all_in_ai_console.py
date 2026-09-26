from pathlib import Path

TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "mission_control"
    / "templates"
    / "all_in_ai.html"
)


def test_console_exposes_real_lifecycle_controls():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "Start Mission" in html
    assert "Verify Read-back" in html
    assert "STOP" in html
    assert "Recover for Review" in html
    assert "read_back_verified" in html
    assert "audit_verified" in html
    assert "hrm_verified" in html


def test_console_does_not_claim_execution_authority():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "cannot approve itself" in html
    assert "execution_granted" in html
    assert "approval_granted" in html
    assert "Human" in html or "human" in html


def test_console_keeps_alien_intelligence_as_research_mode():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "Alien Intelligence" in html
    assert "unconventional research" in html
    assert "Evidence still controls truth claims" in html


def test_console_posts_with_csrf_and_same_origin_credentials():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "X-OAP-CSRF" in html
    assert "credentials:'same-origin'" in html
