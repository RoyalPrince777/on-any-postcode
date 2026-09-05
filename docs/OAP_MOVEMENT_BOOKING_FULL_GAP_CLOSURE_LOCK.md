# OAP Movement + Direct Full Gap Closure Lock

Status: LIVE LOCK TARGET
Owner: Human Authority / Founder
Surface: Private Command Center -> SMI Command -> War Room -> Intelligence
Date: 2026-09-05

## Master rule

Movement Intelligence and Direct Intelligence must never turn green by wording alone.
An Intelligence surface may only be green when it has a registered route, a public/private boundary, a Guardian/Aegis safety result, a proof state, and a safe next gate.

Anything that affects people, money, travel, location, suppliers, reservations, or real-world dispatch remains Human Authority gated.

## Naming lock

Public product name: OAP Direct
System name: Direct Intelligence
Combined surface: Movement + Direct + Map Intelligence
Clean private route: /mission/direct-intelligence
Compatibility route: /mission/booking-intelligence

Use Direct Intelligence for the system. Use booking only as a functional action when referring to a booking request, reservation request, or old compatibility path.

## Placement

```text
SMI Command
└── War Room
    ├── Movement / Map Control
    │   ├── Route proof
    │   ├── Movement request
    │   ├── Match proposal
    │   ├── Tracking consent
    │   ├── Payment-intent boundary
    │   ├── Link Up trip binding
    │   ├── HRM movement receipt
    │   └── Green Gate status
    └── Direct Intelligence
        ├── OAP Direct catalogue
        ├── Quote check
        ├── Buyer hold
        ├── Reservation request
        ├── Founder supply control
        ├── Supplier certification
        ├── Inventory / availability
        ├── Supplier confirmation
        ├── Listing pictures
        ├── HRM Direct receipt
        └── Green Gate status
```

## Clean Intelligence routes

```text
/mission/intelligence
/mission/intelligence-status
/mission/movement-intelligence
/mission/direct-intelligence
/mission/map-intelligence
/mission/maps
/mission/movement-direct-map
/mission/movement-direct-map-pictures
/mission/listing-pictures
/mission/travel-pictures
/mission/listing-photos
```

## Compatibility routes

```text
/mission/booking-intelligence
/mission/movement-booking-map
/mission/movement-booking-map-pictures
/mission/checkpoints/...
/mission/war-room/checkpoints/...
```

Compatibility routes may remain so old links do not break. They are not the preferred system language.

These routes are Founder/private Mission Control intelligence surfaces. They must not dispatch, reserve, charge, approve, migrate, or expose private operational data.

## Movement Intelligence gap closure

### Green / implemented software boundaries

- Public Movement surface route exists: `/movement`.
- Public Movement status route exists: `/movement/status`.
- Private Movement workspace route exists: `/movement/workspace`.
- Private route planning endpoint exists: `/movement/route`.
- Authenticated movement request endpoint exists: `/movement/bookings`.
- Match proposal endpoint exists and must not dispatch anyone: `/movement/bookings/<booking_id>/match`.
- Worker acceptance endpoint exists and must not activate external dispatch: `/movement/matches/<proposal_id>/accept`.
- Tracking consent grant endpoint exists: `/movement/bookings/<booking_id>/tracking/consent`.
- Tracking consent revoke endpoint exists: `DELETE /movement/bookings/<booking_id>/tracking/consent`.
- Tracking point endpoint exists and requires active consent: `/movement/bookings/<booking_id>/tracking/points`.
- Connectivity request endpoint exists and must not activate/install/switch an eSIM: `/movement/esim/requests`.
- Payment intent endpoint exists and must not authorise or capture money: `/movement/bookings/<booking_id>/payment-intents`.
- Trip-to-Link-Up binding endpoint exists: `/movement/bookings/<booking_id>/link-up`.

### Movement gaps now marked as proof-needed, not missing architecture

- Live route matrix proof is needed for 200/302/403 outcomes.
- Movement schema proof is needed before request, match and tracking records are certified.
- HRM movement receipt proof is needed for important movement decisions.
- Green Gate automation must read real Movement Intelligence results.
- Anonymous/private access leak test must prove private movement surfaces fail closed.
- No-consent tracking failure proof must show a safe block.
- Production provider/capacity/monitoring proof is needed before route-production claims.

### Movement locked items

- Real-world dispatch is locked.
- Hidden tracking is blocked.
- Covert location collection is blocked.
- Public precise location leakage is blocked.
- Payment capture is locked.
- eSIM activation/installation/switching is locked.
- Emergency-service or authority claims are blocked.

## Direct Intelligence gap closure

### Green / implemented software boundaries

- Public Travel surface route exists: `/travel`.
- Public OAP Direct route exists: `/travel/direct`.
- Public catalogue API exists: `/travel/api/catalogue`.
- Public direct offers API exists: `/travel/direct/api/offers`.
- Public quote endpoint exists: `/travel/direct/api/quote`.
- Authenticated buyer hold endpoint exists: `/travel/direct/api/hold`.
- Authenticated reservation request endpoint exists: `/travel/direct/api/reservations`.
- Founder supply dashboard exists: `/mission/supply`.
- Founder supply status API exists: `/mission/supply/status`.
- Supplier creation/review/certification endpoints exist under `/mission/supply/suppliers`.
- Listing creation/photo/activation endpoints exist under `/mission/supply/listings`.
- Inventory endpoint exists: `/mission/supply/inventory`.
- Supplier reservation confirmation endpoint exists: `/mission/supply/reservations/confirm`.
- Partner Supply status/import routes intentionally return removed/blocked state.

### Direct Intelligence gaps now marked as proof-needed, not missing architecture

- OAP Direct supplier record must be certified by Founder.
- Commercial terms must be certified before public supply is treated as ready.
- Active listing and photo safety proof must exist.
- Availability/inventory proof must exist.
- Buyer hold proof must exist with CSRF and authenticated identity.
- Reservation lifecycle proof must exist from request to supplier confirmation.
- HRM Direct receipt proof must record quote, hold, reservation and confirmation decisions.
- Green Gate automation must read the real Direct Intelligence state.
- Public claims must remain conservative until supplier and reservation proof exist.

### Listing picture requirements

- Every public OAP Direct listing should expose a cover photo when certified photos exist.
- Listing galleries must use first-party storage.
- Accepted types are JPEG, PNG and WebP.
- Photo rights confirmation is required.
- Private media must never leak through public listing routes.
- External image hosts are not required for OAP Direct listing pictures.

### Direct Intelligence locked items

- External marketplace import is blocked.
- External provider authority is false.
- Payment capture is locked.
- Confirmed reservation claim is locked until supplier confirmation proof exists.
- Commission/revenue claim is locked until commercial receipt exists.
- Refund/cancellation handling must be proven before money flow is certified.
- Any accommodation, travel, ticket or event supply must be direct, certified, and auditable.

## Map Intelligence requirements

- Public map/travel surface must stay clean and human-readable.
- Location hierarchy must follow Postcode -> Borough -> County/Region -> Country -> Continent -> Global.
- Map source health must be checked before public map confidence claims.
- Stale data must be labelled.
- No hidden tracking.
- No fake live-route claims.
- No Google dependency claim unless explicitly configured and approved.
- Production routing remains locked until provider/source, capacity, monitoring, privacy, and Green Gate proof exist.

## Shared Green Gate rule

A Movement, Direct or Map Intelligence surface can only show green when all of the following are true:

1. Route exists.
2. Access boundary is correct.
3. Button/endpoint performs a real safe action or returns a clear locked state.
4. Data source/store exists.
5. Failure is safe.
6. Guardian/Aegis blocks unsafe use.
7. HRM receipt exists for consequential action.
8. Public claim is accurate and not over-stated.
9. Human Authority approves consequential real-world movement, money, reservation, supplier, location, or public claim.

## Final truth board

```text
Movement architecture:          GREEN
Movement route URLs:            GREEN
Movement private boundary:      GUARDED
Movement live route proof:      BUILDING
Movement schema proof:          BUILDING until status is proven
Movement real dispatch:         LOCKED
Movement payment capture:       LOCKED
Movement hidden tracking:       BLOCKED

Direct architecture:            GREEN
Direct route URLs:              GREEN
OAP Direct policy:              GUARDED
Direct supply proof:            BUILDING until certified supplier/listing/inventory exists
Direct listing pictures:        BUILDING until every active listing has certified photos
Direct reservation lifecycle:   BUILDING until confirmed receipt exists
Direct external import:         BLOCKED
Direct payment capture:         LOCKED
Direct confirmed claim:         LOCKED until proof

Map architecture:               GREEN
Map route URLs:                 GREEN
Map source health proof:        BUILDING
Map stale-data guard:           GUARDED
Map hidden tracking:            BLOCKED
Map fake live-route claims:     BLOCKED
Map production routing:         LOCKED until proof
```

## War Room decision

These systems are structurally complete for safe software intelligence surfacing.
They are not fully operationally certified until live route results, schemas, HRM receipts, supplier/inventory evidence, listing-picture evidence, map source-health evidence, and Green Gate automation are proven.

No fake green.
No hidden tracking.
No unsafe dispatch.
No third-party booking authority.
No payment capture without compliance proof.
No confirmed reservation claim without supplier confirmation proof.
