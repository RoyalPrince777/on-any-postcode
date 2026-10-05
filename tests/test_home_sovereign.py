from __future__ import annotations


def test_home_keeps_public_world_without_private_founder_entry(client):
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "YOUR LOCAL" in page
    assert "MARKETPLACE." in page
    assert "Shop local. Sell local." in page
    assert 'href="/the-spot/market"' in page
    assert 'href="/pay/bank"' in page
    assert "Enter My World" in page
    assert 'href="/auth"' not in page
    assert 'href="/mission"' not in page
    assert 'href="/my-world"' not in page
    assert "Founder" not in page
    assert "NEON" not in page
    assert "SMI" not in page
    assert 'href="/world-cup"' not in page

    sport = client.get("/world-cup").get_data(as_text=True)
    assert 'id="live"' in sport
    assert 'id="teams"' in sport
    assert "🇬🇭 Ghana" in sport


def test_public_main_menu_is_commerce_only(client):
    page = client.get("/").get_data(as_text=True)
    nav = page.split('<nav class="bottom"', 1)[1].split("</nav>", 1)[0]

    expected = (
        ("/the-spot/market", "Shop"),
        ("/the-spot/market#sell", "Sell"),
        ("/the-spot/market#orders", "Orders"),
        ("/pay/bank", "Pay"),
    )
    assert nav.count("<a ") == 4
    for href, label in expected:
        assert f'href="{href}"' in nav
        assert label in nav

    for noise in ("The Spot", "Link Up", "Library", "Studio", "HRM", "Guardian", "Settings"):
        assert noise not in nav


def test_public_home_and_sport_keep_only_public_post_forms(client):
    home = client.get("/").get_data(as_text=True)
    sport = client.get("/world-cup").get_data(as_text=True)

    assert 'method="post" action="/signal"' not in home
    for route in ("/room", "/flag"):
        assert f'method="post" action="{route}"' in sport
    assert 'method="post" action="/myworld"' not in home + sport
    assert home.count('name="csrf_token"') == 0
    assert sport.count('name="csrf_token"') == 96


def test_gateway_has_three_validated_mode_links(client):
    page = client.get("/mission").get_data(as_text=True)

    assert 'href="/mission?mode=sovereign"' in page
    assert 'href="/mission?mode=mission"' in page
    assert 'href="/mission?mode=approval"' in page


def test_gateway_shows_seven_oap_intelligence_families(client):
    page = client.get("/mission").get_data(as_text=True)

    for name in (
        "Civic Intelligence",
        "Jungle Book Intelligence",
        "Animal Intelligence",
        "Matrix Intelligence",
        "Civilisation Intelligence",
        "Akan Core Intelligence",
        "Akan Animal Intelligence",
    ):
        assert name in page

    assert "GPT Intelligence" not in page
    assert "Ollama Local Intelligence" not in page



def test_public_dashboard_strips_to_shop_customer_jobs(client):
    page = client.get("/").get_data(as_text=True)
    assert "STRIP OF NOISE" not in page
    for text in ("Signal", "Quick Actions", "OAP Status", "Library", "Studio", "Link Up", "Guardian", "HRM"):
        assert text not in page
    for href in (
        "/the-spot/market",
        "/the-spot/market#sell",
        "/the-spot/market#orders",
        "/pay/bank",
        "/eats",
        "/oap-map",
        "/transport/ride",
    ):
        assert f'href="{href}"' in page


def test_legacy_dashboard_urls_redirect_instead_of_404(client):
    expected = {
        "/sika": "/pay/bank",
        "/guardian": "/transport/ride",
        "/settings": "/enter-my-world?next=/my-world/settings",
        "/hrm": "/enter-my-world?next=/mission",
        "/status": "/healthz",
    }
    for source, target in expected.items():
        response = client.get(source, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].endswith(target)



def test_marketplace_home_and_shop_storefront_are_distinct_surfaces(client):
    home = client.get("/").get_data(as_text=True)
    assert "YOUR LOCAL" in home
    assert "MARKETPLACE." in home
    assert "Shops" in home
    assert "Featured products" in home
    assert 'aria-label="Commerce navigation"' in home

    from pathlib import Path
    source = Path("app.py").read_text(encoding="utf-8")
    assert '@app.get("/shop/<shop_slug>")' in source
    assert '"shop.html"' in source

    shop = Path("templates/shop.html").read_text(encoding="utf-8")
    assert 'aria-label="Shop sections"' in shop
    assert 'aria-label="Shop navigation"' in shop
    assert 'oap-market-basket-v1' in shop
    assert 'class="buy market-add"' in shop
    assert 'href="/the-spot/market#basket"' in shop


def test_marketplace_home_uses_canonical_shop_slug():
    from pathlib import Path
    source = Path("app.py").read_text(encoding="utf-8")
    home = Path("templates/home.html").read_text(encoding="utf-8")
    assert 'item["shop_slug"] = _shop_slug(item.get("seller"))' in source
    assert 'href="/shop/{{ shop.slug }}"' in home
    assert 'href="/shop/{{ product.shop_slug }}"' in home
