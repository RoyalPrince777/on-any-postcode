from pathlib import Path


def test_founder_recovery_has_show_hide_control():
    template = Path('mission_control/templates/founder_recovery.html').read_text(encoding='utf-8')
    assert 'id="founder-code"' in template
    assert 'id="show-code"' in template
    assert ">Show<" in template
    assert "input.type = reveal ? 'text' : 'password'" in template
    assert 'type="submit">Enter SMI</button>' in template
