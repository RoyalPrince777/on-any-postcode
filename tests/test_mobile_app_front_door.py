from pathlib import Path


def test_mobile_app_front_door_exposes_real_controls():
    template = Path("templates/home.html").read_text(encoding="utf-8")

    assert 'aria-label="OAP mobile app controls"' in template
    assert 'href="/linkup"' in template
    assert 'href="/enter-my-world?next=/"' in template
    assert 'href="/on-any-place"' in template
    assert 'href="/the-spot"' in template
    assert '<div class="menu" aria-hidden="true">☰</div>' in template
