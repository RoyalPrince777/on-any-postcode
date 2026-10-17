from __future__ import annotations

from flask import abort, redirect, render_template_string, request, session, url_for
from markupsafe import escape

MARKET_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{{ title }} · OAP Market</title>
<style>
:root{--bg:#07120c;--panel:#0b1f13;--panel2:#102a19;--line:#1f7a3a;--green:#23c55e;--muted:#b8d8bf;--gold:#f2c85b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#fff;font-family:Arial,sans-serif}
a{color:inherit}.shop-head{position:sticky;top:0;z-index:20;background:#08170ef2;border-bottom:1px solid var(--line);backdrop-filter:blur(12px)}
.head-row{max-width:1180px;margin:auto;padding:10px 16px;display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center}
.brand{text-decoration:none;font-weight:950;white-space:nowrap}.search{display:flex;background:#0d2114;border:1px solid #285f39;border-radius:999px;overflow:hidden}
.search input{width:100%;min-width:0;background:transparent;border:0;color:#fff;padding:11px 14px;outline:none}.search button{border:0;background:var(--green);font-weight:900;padding:0 16px}
.bag{border:1px solid #356844;padding:9px 12px;border-radius:999px;text-decoration:none;font-weight:900;white-space:nowrap}
.shell{max-width:1180px;margin:auto;padding:20px 16px 90px}.hero{display:grid;grid-template-columns:1fr auto;gap:18px;align-items:end;padding:14px 0 18px}
.hero h1{font-size:clamp(2.5rem,6vw,5.2rem);line-height:.91;margin:.08em 0}.eyebrow{color:var(--gold);font-size:.76rem;letter-spacing:.17em;font-weight:950;text-transform:uppercase}
.hero p{max-width:680px;color:var(--muted);font-size:1.06rem}.hero-actions{display:flex;gap:8px;flex-wrap:wrap}
.btn,.btn2,button{display:inline-flex;align-items:center;justify-content:center;min-height:44px;border-radius:12px;padding:10px 14px;font-weight:900;text-decoration:none;cursor:pointer}
.btn,button{background:var(--green);color:#041007;border:0}.btn2{border:1px solid #356844;background:#0a180f;color:#fff}
.chips{display:flex;gap:8px;overflow:auto;padding:2px 0 14px;scrollbar-width:none}.chip{border:1px solid #356844;border-radius:999px;padding:9px 13px;text-decoration:none;font-weight:850;white-space:nowrap}
.chip.active{background:#173d24;border-color:#46d978}.bar{display:flex;justify-content:space-between;gap:10px;align-items:center;color:var(--muted);margin:4px 0 14px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.product{border:1px solid #1f5932;background:var(--panel);border-radius:18px;overflow:hidden;display:flex;flex-direction:column;min-height:350px}
.art{aspect-ratio:4/3;background:linear-gradient(145deg,#173d24,#09180e);display:grid;place-items:center;overflow:hidden;text-decoration:none}.art img{width:100%;height:100%;object-fit:cover}.art span{font-size:3rem}
.body{padding:14px;display:flex;flex-direction:column;gap:8px;height:100%}.meta{color:#8fc69d;font-size:.76rem;font-weight:900;text-transform:uppercase;letter-spacing:.07em}.product h3{margin:0;font-size:1.04rem}
.seller{color:var(--muted);font-size:.88rem}.price{font-size:1.18rem;font-weight:950}.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:auto}.actions form{margin:0}.actions button,.actions a{width:100%}
.empty{text-align:center;padding:50px 20px;border:1px dashed #3d6b49;border-radius:20px;background:#0a180f}.empty .ico{font-size:3.2rem}
.product-page{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);gap:24px}.product-page .art{border-radius:20px;min-height:440px}.buy{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:22px;align-self:start;position:sticky;top:82px}
.buy h1{font-size:clamp(2rem,5vw,3.6rem);line-height:.96;margin:.18em 0}.qty{display:grid;grid-template-columns:90px 1fr;gap:10px;align-items:end}.qty input{width:100%;padding:11px;border-radius:10px;border:1px solid #356844;background:#08170e;color:#fff}
.note{margin-top:15px;padding:12px 14px;background:#17190c;border-left:3px solid var(--gold);color:#f5e7b0;border-radius:8px}
.bag-list{display:grid;gap:10px}.bag-row{display:grid;grid-template-columns:82px 1fr auto;gap:14px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:12px}.thumb{width:82px;height:82px;border-radius:12px;background:#123d22;display:grid;place-items:center;overflow:hidden;text-decoration:none}.thumb img{width:100%;height:100%;object-fit:cover}
.controls{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.controls input{width:70px;padding:10px;border-radius:10px;border:1px solid #356844;background:#08170e;color:#fff}.total{display:flex;justify-content:space-between;font-size:1.25rem;font-weight:950;padding:18px 2px}
.mobile-dock{display:none}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.hero{grid-template-columns:1fr}.product-page{grid-template-columns:1fr}.buy{position:static}}
@media(max-width:620px){.head-row{grid-template-columns:1fr auto}.search{grid-column:1/-1;grid-row:2}.shell{padding:14px 10px 86px}.grid{gap:9px}.body{padding:11px}.actions{grid-template-columns:1fr}.actions .btn2{display:none}.bag-row{grid-template-columns:62px 1fr}.thumb{width:62px;height:62px}.bag-row .right{grid-column:2}.mobile-dock{position:fixed;display:grid;grid-template-columns:repeat(3,1fr);left:8px;right:8px;bottom:max(8px,env(safe-area-inset-bottom));z-index:30;background:#07120cef;border:1px solid #285f39;border-radius:16px;padding:7px;backdrop-filter:blur(12px)}.mobile-dock a{padding:10px 6px;text-align:center;text-decoration:none;font-size:.78rem;font-weight:900}.hero h1{font-size:3rem}}
</style>
</head>
<body>
<header class="shop-head">
  <div class="head-row">
    <a class="brand" href="/market">🌍 OAP MARKET</a>
    <form class="search" action="/market" method="get">
      <input name="q" value="{{ query }}" placeholder="Search products, sellers, categories" aria-label="Search OAP Market">
      <button type="submit">Search</button>
    </form>
    <a class="bag" href="/market/bag">Bag · {{ bag_count }}</a>
  </div>
</header>
{{ body|safe }}
<nav class="mobile-dock" aria-label="Market navigation">
  <a href="/market">🛍️<br>Shop</a><a href="/market/bag">👜<br>Bag</a><a href="/">🌍<br>OAP World</a>
</nav>
</body>
</html>
"""

def _bag() -> dict[str, int]:
    raw = session.get("market_bag") or {}
    clean: dict[str, int] = {}
    for key, value in raw.items():
        try:
            product_id = str(int(key))
            quantity = max(1, min(20, int(value)))
        except (TypeError, ValueError):
            continue
        clean[product_id] = quantity
    if clean != raw:
        session["market_bag"] = clean
        session.modified = True
    return clean

def _money(minor: int, currency: str = "GBP") -> str:
    code = str(currency or "GBP").upper()
    prefix = "£" if code == "GBP" else f"{code} "
    return f"{prefix}{int(minor) / 100:.2f}"

def register_market_storefront(app, db):
    def render_shop(title: str, body: str, *, query: str = ""):
        return render_template_string(
            MARKET_TEMPLATE,
            title=title,
            body=body,
            query=query,
            bag_count=sum(_bag().values()),
        )

    @app.get("/market")
    def market():
        query = " ".join((request.args.get("q") or "").strip().split())
        category = " ".join((request.args.get("category") or "").strip().split())
        conn = db()
        categories = [str(row["category"]) for row in conn.execute(
            "SELECT DISTINCT category FROM market_products WHERE state='LIVE' ORDER BY category COLLATE NOCASE"
        ).fetchall()]
        clauses = ["state='LIVE'"]
        params: list[object] = []
        if query:
            clauses.append("(title LIKE ? OR description LIKE ? OR seller_name LIKE ? OR category LIKE ?)")
            like = f"%{query}%"
            params.extend([like, like, like, like])
        if category:
            clauses.append("category=?")
            params.append(category)
        products = conn.execute(
            f"SELECT * FROM market_products WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT 80",
            params,
        ).fetchall()
        conn.close()

        chip_html = [
            f'<a class="chip{" active" if not category else ""}" href="/market">Shop all</a>'
        ]
        for item in categories:
            active = " active" if category == item else ""
            chip_html.append(
                f'<a class="chip{active}" href="/market?category={escape(item)}">{escape(item)}</a>'
            )

        cards = []
        for product in products:
            art = (
                f'<img src="{escape(product["image_url"])}" alt="">'
                if product["image_url"] else "<span>🛍️</span>"
            )
            cards.append(f"""
            <article class="product">
              <a class="art" href="/market/product/{product['id']}">{art}</a>
              <div class="body">
                <div class="meta">{escape(product['category'])}</div>
                <h3>{escape(product['title'])}</h3>
                <div class="seller">by {escape(product['seller_name'] or 'OAP Market')}</div>
                <div class="price">{_money(product['price_minor'], product['currency'])}</div>
                <div class="actions">
                  <a class="btn2" href="/market/product/{product['id']}">View</a>
                  <form method="post" action="/market/bag/add/{product['id']}"><button type="submit">Add to bag</button></form>
                </div>
              </div>
            </article>
            """)

        if cards:
            listing = '<div class="grid">' + "".join(cards) + "</div>"
        else:
            listing = """
            <div class="empty">
              <div class="ico">🛍️</div>
              <h2>No live products match this view</h2>
              <p>OAP Market only renders products actually marked LIVE. Fake stock is not inserted to make the shop look busy.</p>
              <a class="btn2" href="/market">Clear filters</a>
            </div>
            """

        body = f"""
        <main class="shell">
          <section class="hero">
            <div>
              <div class="eyebrow">ON ANY POSTCODE · MARKET</div>
              <h1>Shop the world.<br>Start local.</h1>
              <p>Clothing, creator goods, music merchandise, local products and OAP collections through one storefront.</p>
            </div>
            <div class="hero-actions"><a class="btn" href="/market/bag">Open bag</a><a class="btn2" href="/">OAP World</a></div>
          </section>
          <nav class="chips" aria-label="Market categories">{''.join(chip_html)}</nav>
          <div class="bar"><span>{len(products)} product{'s' if len(products) != 1 else ''}</span><span>Only LIVE inventory shown</span></div>
          {listing}
        </main>
        """
        return render_shop("Shop", body, query=query)

    @app.get("/market/product/<int:product_id>")
    def market_product(product_id: int):
        conn = db()
        product = conn.execute(
            "SELECT * FROM market_products WHERE id=? AND state='LIVE'", (product_id,)
        ).fetchone()
        conn.close()
        if product is None:
            abort(404)
        art = f'<img src="{escape(product["image_url"])}" alt="">' if product["image_url"] else "<span>🛍️</span>"
        body = f"""
        <main class="shell">
          <div class="product-page">
            <div class="art">{art}</div>
            <section class="buy">
              <div class="meta">{escape(product['category'])}</div>
              <h1>{escape(product['title'])}</h1>
              <div class="seller">by {escape(product['seller_name'] or 'OAP Market')}</div>
              <div class="price">{_money(product['price_minor'], product['currency'])}</div>
              <p>{escape(product['description'] or '')}</p>
              <form method="post" action="/market/bag/add/{product['id']}">
                <div class="qty">
                  <label>Qty<input type="number" name="quantity" min="1" max="20" value="1"></label>
                  <button type="submit">Add to bag</button>
                </div>
              </form>
              <div class="note">Browsing and bag actions are first-party. Payment only advances when the authorised OAP payment/provider path is configured.</div>
            </section>
          </div>
        </main>
        """
        return render_shop(str(product["title"]), body)

    @app.post("/market/bag/add/<int:product_id>")
    def market_bag_add(product_id: int):
        conn = db()
        product = conn.execute(
            "SELECT id FROM market_products WHERE id=? AND state='LIVE'", (product_id,)
        ).fetchone()
        conn.close()
        if product is None:
            abort(404)
        try:
            quantity = max(1, min(20, int(request.form.get("quantity") or 1)))
        except ValueError:
            quantity = 1
        bag = _bag()
        key = str(product_id)
        bag[key] = min(20, bag.get(key, 0) + quantity)
        session["market_bag"] = bag
        session.modified = True
        return redirect(request.referrer or url_for("market_bag"))

    @app.post("/market/bag/update/<int:product_id>")
    def market_bag_update(product_id: int):
        bag = _bag()
        key = str(product_id)
        if key not in bag:
            return redirect(url_for("market_bag"))
        if request.form.get("action") == "remove":
            bag.pop(key, None)
        else:
            try:
                quantity = int(request.form.get("quantity") or 1)
            except ValueError:
                quantity = 1
            if quantity <= 0:
                bag.pop(key, None)
            else:
                bag[key] = min(20, quantity)
        session["market_bag"] = bag
        session.modified = True
        return redirect(url_for("market_bag"))

    @app.get("/market/bag")
    def market_bag():
        bag = _bag()
        ids = [int(key) for key in bag]
        products = []
        if ids:
            conn = db()
            marks = ",".join("?" for _ in ids)
            products = conn.execute(
                f"SELECT * FROM market_products WHERE state='LIVE' AND id IN ({marks})", ids
            ).fetchall()
            conn.close()

        available = {str(product["id"]): product for product in products}
        removed = [key for key in bag if key not in available]
        if removed:
            for key in removed:
                bag.pop(key, None)
            session["market_bag"] = bag
            session.modified = True

        rows = []
        total = 0
        currency = "GBP"
        for key, quantity in bag.items():
            product = available.get(key)
            if product is None:
                continue
            line_total = int(product["price_minor"]) * quantity
            total += line_total
            currency = product["currency"]
            art = f'<img src="{escape(product["image_url"])}" alt="">' if product["image_url"] else "🛍️"
            rows.append(f"""
            <div class="bag-row">
              <a class="thumb" href="/market/product/{product['id']}">{art}</a>
              <div><strong>{escape(product['title'])}</strong><div class="seller">{escape(product['category'])}</div><div>{_money(product['price_minor'], product['currency'])} each</div></div>
              <div class="right">
                <form class="controls" method="post" action="/market/bag/update/{product['id']}">
                  <input name="quantity" type="number" min="0" max="20" value="{quantity}">
                  <button type="submit">Update</button>
                  <button type="submit" name="action" value="remove" class="btn2">Remove</button>
                </form>
                <strong>{_money(line_total, product['currency'])}</strong>
              </div>
            </div>
            """)

        if not rows:
            body = """
            <main class="shell"><h1>Your bag</h1><div class="empty"><div class="ico">👜</div><h2>Your bag is empty</h2><p>Add a live product from OAP Market.</p><a class="btn" href="/market">Shop Market</a></div></main>
            """
            return render_shop("Bag", body)

        body = f"""
        <main class="shell">
          <div class="eyebrow">OAP MARKET</div><h1>Your bag</h1>
          <div class="bag-list">{''.join(rows)}</div>
          <div class="total"><span>Total</span><span>{_money(total, currency)}</span></div>
          <div class="hero-actions"><a class="btn2" href="/market">Keep shopping</a><a class="btn" href="/market/checkout">Review checkout</a></div>
        </main>
        """
        return render_shop("Bag", body)

    @app.get("/market/checkout")
    def market_checkout():
        if not _bag():
            return redirect(url_for("market_bag"))
        body = """
        <main class="shell">
          <div class="eyebrow">CHECKOUT</div><h1>Review checkout</h1>
          <div class="empty" style="text-align:left">
            <h2>Bag is ready</h2>
            <p>Your selections are preserved in the OAP Market bag.</p>
            <div class="note">Payment execution is intentionally not enabled in this public storefront. Production checkout connects to the governed OAP Commerce → payment/SIKA → Supplier Bridge → POD route only when that authorised runtime is configured.</div>
            <p><a class="btn2" href="/market/bag">Back to bag</a></p>
          </div>
        </main>
        """
        return render_shop("Checkout", body)
