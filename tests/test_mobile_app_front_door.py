from pathlib import Path


def test_mobile_app_front_door_exposes_only_commerce_controls():
    template = Path("templates/home.html").read_text(encoding="utf-8")

    assert 'aria-label="Commerce navigation"' in template
    assert 'href="/the-spot/market"' in template
    assert 'href="/sell"' in template
    assert 'href="/orders"' in template
    assert 'href="/pay/bank"' in template
    assert 'href="/eats"' in template
    assert 'href="/oap-map"' in template
    assert 'href="/transport/ride"' in template
    assert 'href="/enter-my-world?next=/"' in template
    assert '.bottom{position:fixed' in template
    assert 'env(safe-area-inset-bottom)' in template
    assert "/linkup" not in template
    assert "/library" not in template
    assert "/studio" not in template
