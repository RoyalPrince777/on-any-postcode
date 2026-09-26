from pathlib import Path


def test_mobile_app_front_door_exposes_real_controls():
    template = Path("templates/home.html").read_text(encoding="utf-8")

    assert 'aria-label="OAP mobile app controls"' in template
    assert 'href="/linkup"' in template
    assert 'href="/enter-my-world?next=/"' in template
    assert 'href="/on-any-place"' in template
    assert 'href="/the-spot"' in template
    assert '<details class="menu">' in template
    assert 'aria-label="Open OAP menu"' in template
    assert 'class="menu-panel"' in template
    assert '.mobile-app-dock{position:fixed' in template
    assert 'env(safe-area-inset-bottom)' in template
