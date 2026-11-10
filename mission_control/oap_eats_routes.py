"""Public OAP Eats software surface."""
from __future__ import annotations

from flask import Blueprint, jsonify, make_response, render_template_string, request

from . import oap_eats, oap_eats_fulfilment, oap_eats_store, web_security

bp = Blueprint("oap_eats", __name__)


def _no_store(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0d0c">
<title>OAP Eats</title>
<style>
:root{color-scheme:dark;--bg:#0b0d0c;--panel:#131614;--panel2:#191d1a;--line:#29302b;--gold:#f0c85c;--green:#7ee2a8;--muted:#9aa49d;--text:#f7f8f7}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,sans-serif}
body{min-height:100vh}.app{max-width:760px;margin:auto;padding:env(safe-area-inset-top) 16px calc(92px + env(safe-area-inset-bottom))}
.top{display:flex;align-items:center;justify-content:space-between;padding:16px 0 10px;position:sticky;top:0;background:linear-gradient(var(--bg) 72%,transparent);z-index:3}
.brand{display:flex;gap:11px;align-items:center;text-decoration:none;color:var(--text)}.mark{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(145deg,#2b2412,#13130f);border:1px solid #6b5922;font-weight:900;color:var(--gold)}
.brand strong{display:block;font-size:1.02rem}.brand small{color:var(--muted)}.icon-btn{width:42px;height:42px;border-radius:14px;border:1px solid var(--line);background:var(--panel);color:var(--text);display:grid;place-items:center;text-decoration:none}
.hero{padding:22px 0 10px}.eyebrow{font-size:.76rem;letter-spacing:.12em;color:var(--gold);font-weight:900}.hero h1{font-size:clamp(2rem,9vw,3.6rem);line-height:.98;margin:.45rem 0}.hero p{margin:.6rem 0;color:#c5cbc7;max-width:520px}
.location{display:flex;gap:10px;margin:16px 0}.location a{flex:1;display:flex;align-items:center;justify-content:space-between;padding:15px 16px;border-radius:18px;background:var(--panel);border:1px solid var(--line);text-decoration:none;color:var(--text)}
.location span{color:var(--muted);font-size:.88rem}.primary{display:flex!important;justify-content:center!important;background:var(--gold)!important;color:#17130a!important;border-color:#f6d879!important;font-weight:900;min-width:124px}
.section-head{display:flex;justify-content:space-between;align-items:end;margin:24px 2px 12px}.section-head h2{margin:0;font-size:1.15rem}.section-head a{color:var(--gold);text-decoration:none;font-size:.9rem}
.actions{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.action{min-height:118px;padding:16px;border-radius:22px;border:1px solid var(--line);background:linear-gradient(145deg,var(--panel2),var(--panel));text-decoration:none;color:var(--text);display:flex;flex-direction:column;justify-content:space-between}
.action .emoji{font-size:1.65rem}.action strong{font-size:1.03rem}.action span{font-size:.82rem;color:var(--muted);line-height:1.3}
.track{padding:16px;border:1px solid var(--line);border-radius:22px;background:var(--panel)}.track form{display:flex;gap:8px}.track input{min-width:0;flex:1;border:1px solid #353c37;background:#0e100f;color:var(--text);padding:13px 14px;border-radius:14px;outline:none}.track input:focus{border-color:#806d2d}.track button{border:0;border-radius:14px;padding:0 17px;background:var(--gold);color:#17130a;font-weight:900}.track-result{margin-top:12px;display:none}.track-result.show{display:block}.order-card{padding:14px;border-radius:16px;background:#0f1210;border:1px solid var(--line)}.order-row{display:flex;justify-content:space-between;gap:12px;margin:5px 0}.order-row span{color:var(--muted)}.pill{display:inline-flex;padding:5px 9px;border-radius:999px;background:#173322;color:var(--green);font-size:.76rem;font-weight:800;text-transform:capitalize}
.roles{display:flex;gap:8px;overflow:auto;padding-bottom:4px}.role{white-space:nowrap;padding:10px 13px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:#d9dedb;text-decoration:none;font-size:.85rem}
.truth{margin-top:22px;padding:14px 15px;border-radius:16px;border:1px solid #26322a;background:#101612;color:#a9b6ad;font-size:.82rem;line-height:1.45}.truth b{color:var(--green)}
.bottom{position:fixed;left:50%;bottom:0;transform:translateX(-50%);width:min(760px,100%);display:grid;grid-template-columns:repeat(5,1fr);padding:8px 10px calc(8px + env(safe-area-inset-bottom));background:rgba(13,15,14,.96);border-top:1px solid var(--line);backdrop-filter:blur(16px);z-index:5}
.bottom a{display:grid;gap:3px;place-items:center;text-decoration:none;color:var(--muted);font-size:.68rem;padding:7px 2px;border-radius:12px}.bottom a.active{color:var(--gold);background:#211d11}.bottom b{font-size:1.05rem}
@media(min-width:620px){.actions{grid-template-columns:repeat(4,1fr)}.action{min-height:136px}}
</style>
</head>
<body>
<main class="app">
<header class="top">
<a class="brand" href="/eats"><span class="mark">OAP</span><span><strong>Eats</strong><small>Find it. Order it. Bring it.</small></span></a>
<a class="icon-btn" href="/transport" aria-label="Open transport">↗</a>
</header>
<section class="hero">
<div class="eyebrow">ON ANY POSTCODE · EATS</div>
<h1>Food around<br>your world.</h1>
<p>One food door connected to OAP Market, OAP World, SIKA and the shared Rides movement engine.</p>
</section>
<div class="location">
<a href="/oap-map"><div><strong>📍 Choose your postcode</strong><br><span>Open OAP World map</span></div><b>›</b></a>
<a class="primary" href="/market">Explore food</a>
</div>
<div class="section-head"><h2>What do you want to do?</h2></div>
<section class="actions">
<a class="action" href="/market"><span class="emoji">🍲</span><div><strong>Browse food</strong><span>Open merchants and products in OAP Market.</span></div></a>
<a class="action" href="/oap-map"><span class="emoji">🗺️</span><div><strong>Explore map</strong><span>Move from postcode to place using OAP World.</span></div></a>
<a class="action" href="/pay/bank"><span class="emoji">🪙</span><div><strong>SIKA</strong><span>Open the payment and value surface.</span></div></a>
<a class="action" href="/transport"><span class="emoji">🚗</span><div><strong>Rides</strong><span>Open shared movement and transport.</span></div></a>
</section>
<div class="section-head"><h2>Track an order</h2><a href="/eats/order-states">Order states</a></div>
<section class="track">
<form id="track-form">
<input id="order-id" name="order_id" autocomplete="off" placeholder="Paste your order ID" aria-label="Order ID">
<button type="submit">Track</button>
</form>
<div id="track-result" class="track-result" role="status" aria-live="polite"></div>
</section>
<div class="section-head"><h2>Your role</h2></div>
<div class="roles">
<a class="role" href="/market">Customer · browse & order</a>
<a class="role" href="/market">Merchant · catalogue & orders</a>
<a class="role" href="/transport">Courier · movement jobs</a>
<a class="role" href="/eats/status">System status</a>
</div>
<div class="truth"><b>● Software surface active.</b> Real merchant trading, payment settlement and courier execution stay evidence-gated. Physical operations are outside this software build.</div>
</main>
<nav class="bottom" aria-label="OAP Eats navigation">
<a class="active" href="/eats"><b>⌂</b><span>Eats</span></a>
<a href="/market"><b>⌕</b><span>Explore</span></a>
<a href="/oap-map"><b>◎</b><span>World</span></a>
<a href="/transport"><b>↗</b><span>Rides</span></a>
<a href="/pay/bank"><b>◈</b><span>SIKA</span></a>
</nav>
<script>
(()=>{
 const form=document.querySelector('#track-form'),input=document.querySelector('#order-id'),out=document.querySelector('#track-result');
 const esc=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
 form.addEventListener('submit',async event=>{
  event.preventDefault();const id=input.value.trim();
  if(!id){out.className='track-result show';out.textContent='Enter an order ID.';return}
  out.className='track-result show';out.textContent='Checking order…';
  try{
   const response=await fetch('/eats/orders/'+encodeURIComponent(id),{credentials:'same-origin',cache:'no-store'});
   const data=await response.json().catch(()=>({}));
   if(!response.ok){
    const code=data?.error?.code||'order_unavailable';
    out.innerHTML='<div class="order-card">Order could not be opened · '+esc(code.replaceAll('_',' '))+'</div>';return
   }
   const amount=(Number(data.amount_minor||0)/100).toFixed(2);
   out.innerHTML='<div class="order-card"><div class="order-row"><strong>Order</strong><span>'+esc(data.order_id)+'</span></div><div class="order-row"><span>Status</span><b class="pill">'+esc(data.state)+'</b></div><div class="order-row"><span>Total</span><b>'+esc(data.currency)+' '+amount+'</b></div><div class="order-row"><span>Fulfilment</span><b>'+esc(data.fulfilment_mode)+'</b></div></div>';
  }catch{
   out.innerHTML='<div class="order-card">Order service is temporarily unavailable.</div>'
  }
 });
})();
</script>
</body>
</html>"""


@bp.get("/eats")
def eats_home():
    return _no_store(make_response(render_template_string(_PAGE), 200))


@bp.get("/eats/status")
def eats_status():
    return _no_store(make_response(jsonify(oap_eats.status()), 200))


@bp.get("/eats/app-config")
def eats_app_config():
    return _no_store(make_response(jsonify({
        "product": "OAP Eats",
        "front_door": "/eats",
        "navigation": {
            "eats": "/eats",
            "explore": "/market",
            "world": "/oap-map",
            "rides": "/transport",
            "sika": "/pay/bank",
        },
        "roles": {
            key: list(role.permissions) for key, role in oap_eats.ROLES.items()
        },
        "physical_operations_in_scope": False,
        "human_authority_final": True,
    }), 200))


@bp.get("/eats/orders/<order_id>")
@web_security.login_required(api=True)
def read_order(order_id: str):
    identity = web_security.authenticated_identity()
    try:
        result = oap_eats_store.STORE.read_order(
            order_id=order_id,
            identity_id=identity,
        )
        return _no_store(make_response(jsonify(result), 200))
    except PermissionError as exc:
        return _error(str(exc) or "eats_access_denied", 403)
    except ValueError as exc:
        return _error(str(exc) or "invalid_eats_order", 400)
    except RuntimeError:
        return _error("eats_store_unavailable", 503)


@bp.get("/eats/order-states")
def eats_order_states():
    return _no_store(make_response(jsonify({
        "states": [state.value for state in oap_eats.EatsOrderState],
        "human_authority_final": True,
    }), 200))


def _error(code: str, status: int):
    return _no_store(make_response(jsonify(error={"code": code}), status))


@bp.post("/eats/orders")
@web_security.login_required(api=True)
def create_order():
    identity = web_security.authenticated_identity()
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("json_object_required", 400)
    try:
        result = oap_eats_store.STORE.create_order(
            customer_identity_id=identity,
            merchant_id=body.get("merchant_id"),
            items=body.get("items"),
            amount_minor=body.get("amount_minor"),
            currency=body.get("currency"),
            fulfilment_mode=body.get("fulfilment_mode"),
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
        return _no_store(make_response(jsonify(result), 201))
    except PermissionError as exc:
        return _error(str(exc) or "eats_access_denied", 403)
    except ValueError as exc:
        code = str(exc) or "invalid_eats_order"
        return _error(code, 409 if code == "idempotency_conflict" else 400)
    except RuntimeError:
        return _error("eats_store_unavailable", 503)


@bp.post("/eats/orders/<order_id>/state")
@web_security.login_required(api=True)
def transition_order(order_id: str):
    identity = web_security.authenticated_identity()
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("json_object_required", 400)
    try:
        result = oap_eats_store.STORE.transition(
            order_id=order_id,
            actor_identity_id=identity,
            target_state=body.get("state"),
        )
        return _no_store(make_response(jsonify(result), 200))
    except PermissionError as exc:
        return _error(str(exc) or "eats_access_denied", 403)
    except ValueError as exc:
        return _error(str(exc) or "invalid_eats_transition", 400)
    except RuntimeError:
        return _error("eats_store_unavailable", 503)


@bp.post("/eats/orders/<order_id>/payment")
@web_security.login_required(api=True)
def bind_order_payment(order_id: str):
    identity = web_security.authenticated_identity()
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("json_object_required", 400)
    try:
        result = oap_eats_fulfilment.bind_payment(
            order_id=order_id,
            customer_identity_id=identity,
            payment_id=body.get("payment_id"),
        )
        return _no_store(make_response(jsonify(result), 200))
    except PermissionError as exc:
        return _error(str(exc) or "eats_access_denied", 403)
    except ValueError as exc:
        return _error(str(exc) or "invalid_eats_payment", 400)
    except RuntimeError:
        return _error("eats_payment_bridge_unavailable", 503)


@bp.post("/eats/orders/<order_id>/delivery")
@web_security.login_required(api=True)
def create_order_delivery(order_id: str):
    identity = web_security.authenticated_identity()
    if not web_security.csrf_valid(request):
        return _error("csrf_failed", 403)
    if not web_security.PUBLIC_WRITE_LIMITER.allow(identity):
        return _error("rate_limited", 429)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("json_object_required", 400)
    try:
        result = oap_eats_fulfilment.create_delivery(
            order_id=order_id,
            customer_identity_id=identity,
            pickup=body.get("pickup"),
            destination=body.get("destination"),
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
        return _no_store(make_response(jsonify(result), 201))
    except PermissionError as exc:
        return _error(str(exc) or "eats_access_denied", 403)
    except ValueError as exc:
        code = str(exc) or "invalid_eats_delivery"
        return _error(code, 409 if code == "idempotency_conflict" else 400)
    except RuntimeError:
        return _error("eats_delivery_bridge_unavailable", 503)


@bp.get("/eats/fulfilment-status")
def eats_fulfilment_status():
    return _no_store(make_response(jsonify(oap_eats_fulfilment.status()), 200))
