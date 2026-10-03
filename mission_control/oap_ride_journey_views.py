"""Private OAP Ride current-journey surface."""
from __future__ import annotations

from flask import Blueprint, make_response, render_template_string

from . import movement_workspace, web_security

bp = Blueprint("oap_ride_journey_views", __name__)

PAGE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Current Journey · OAP Ride</title><style>
body{margin:0;background:#080808;color:#fff;font-family:system-ui}main{max-width:760px;margin:auto;padding:18px}
a{color:#aaa}.card{border:1px solid #333;border-radius:18px;padding:16px;margin:12px 0;background:#111}
button,input,textarea{width:100%;padding:13px;margin-top:8px;border-radius:12px;border:1px solid #444;background:#181818;color:#fff}
button{font-weight:800}.state{color:#f1d36b;font-weight:800}.result{color:#aaa;min-height:1.2em}
</style></head><body><main>
<a href="/transport/my">← My Transport</a><h1>Current Journey</h1>

<h2>Rider</h2>
{% for booking in snapshot.bookings if booking.service_type == 'ride' and booking.state in ['ACCEPTED','IN_PROGRESS','COMPLETED'] %}
<section class="card" data-booking="{{ booking.booking_id }}"><div class="state">{{ booking.state }}</div>
<h3>{{ booking.pickup_label }} → {{ booking.destination_label }}</h3>
{% if booking.state == 'ACCEPTED' %}<button class="issue-code">Journey Code</button>{% endif %}
{% if booking.state == 'COMPLETED' %}<button class="receipt">Receipt</button>
<input class="rating" inputmode="numeric" min="1" max="5" placeholder="Rating 1-5"><textarea class="note" maxlength="500" placeholder="Feedback"></textarea><button class="feedback">Send Feedback</button>{% endif %}
<button class="guardian-on">Enable Guardian</button><button class="guardian-off">Disable Guardian</button><input class="trusted" maxlength="160" placeholder="Trusted contact reference"><button class="incident">Report Safety Concern</button><p class="result"></p></section>
{% else %}<p>No active rider journey.</p>{% endfor %}

<h2>Driver</h2>
{% for item in snapshot.worker_matches if item.service_type == 'ride' and item.proposal_state == 'ACCEPTED' and item.booking_state in ['ACCEPTED','IN_PROGRESS','COMPLETED'] %}
<section class="card" data-booking="{{ item.booking_id }}"><div class="state">{{ item.booking_state }}</div>
<h3>{{ item.pickup_zone }} → {{ item.destination_zone }}</h3>
{% if item.booking_state == 'ACCEPTED' %}<input class="journey-code" inputmode="numeric" maxlength="6" placeholder="Journey Code"><button class="start">Start Journey</button>{% endif %}
{% if item.booking_state == 'IN_PROGRESS' %}<button class="complete">Complete Journey</button>{% endif %}
{% if item.booking_state == 'COMPLETED' %}<button class="receipt">Receipt</button>
<input class="rating" inputmode="numeric" min="1" max="5" placeholder="Rating 1-5"><textarea class="note" maxlength="500" placeholder="Feedback"></textarea><button class="feedback">Send Feedback</button>{% endif %}
<p class="result"></p></section>
{% else %}<p>No active driver journey.</p>{% endfor %}

<script>
const csrf={{ oap_csrf_token|tojson }};
async function api(path,method="GET",body){
 const headers={"X-OAP-CSRF":csrf}; const options={method,headers,credentials:"same-origin"};
 if(body!==undefined){headers["Content-Type"]="application/json";options.body=JSON.stringify(body);}
 const r=await fetch(path,options); const p=await r.json().catch(()=>({}));
 if(!r.ok) throw new Error((p.error||{}).code||"Request failed"); return p;
}
document.querySelectorAll(".card").forEach(card=>{
 const id=card.dataset.booking, out=card.querySelector(".result");
 const run=async(fn)=>{try{out.textContent=await fn();}catch(e){out.textContent=e.message;}};
 card.querySelector(".issue-code")?.addEventListener("click",()=>run(async()=>{const p=await api("/transport/ride/bookings/"+id+"/journey-code","POST");return "Journey Code: "+p.journey_code;}));
 card.querySelector(".start")?.addEventListener("click",()=>run(async()=>{const code=card.querySelector(".journey-code").value;await api("/transport/ride/bookings/"+id+"/start","POST",{journey_code:code});location.reload();return "Started";}));
 card.querySelector(".complete")?.addEventListener("click",()=>run(async()=>{await api("/transport/ride/bookings/"+id+"/complete","POST");location.reload();return "Completed";}));
 card.querySelector(".receipt")?.addEventListener("click",()=>run(async()=>{const p=await api("/transport/ride/bookings/"+id+"/receipt");return "Receipt · "+p.payment_state+(p.amount_minor===null?"":" · "+p.amount_minor+" "+(p.currency||""));}));
 card.querySelector(".feedback")?.addEventListener("click",()=>run(async()=>{const rating=card.querySelector(".rating").value,note=card.querySelector(".note").value;await api("/transport/ride/bookings/"+id+"/feedback","POST",{rating:rating,note:note});return "Feedback saved";}));
 card.querySelector(".guardian-on")?.addEventListener("click",()=>run(async()=>{const ref=card.querySelector(".trusted")?.value||"";await api("/transport/ride/bookings/"+id+"/guardian","POST",{enabled:true,trusted_contact_ref:ref});return "Guardian enabled";}));
 card.querySelector(".guardian-off")?.addEventListener("click",()=>run(async()=>{await api("/transport/ride/bookings/"+id+"/guardian","POST",{enabled:false,trusted_contact_ref:""});return "Guardian disabled";}));
 card.querySelector(".incident")?.addEventListener("click",()=>run(async()=>{await api("/transport/ride/bookings/"+id+"/guardian/incidents","POST",{kind:"SAFETY_CONCERN",note:""});return "Safety concern recorded";}));
});
</script></main></body></html>"""


@bp.get("/transport/ride/current")
@web_security.login_required()
def current_journey():
    identity = web_security.authenticated_identity()
    snapshot = movement_workspace.snapshot(identity)
    response = make_response(render_template_string(PAGE, snapshot=snapshot))
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
