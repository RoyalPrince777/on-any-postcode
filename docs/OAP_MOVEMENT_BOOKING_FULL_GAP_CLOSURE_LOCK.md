# OAP Movement + Booking Full Gap Closure Lock

Status: LIVE LOCK TARGET
Owner: Human Authority / Founder
Surface: Private Command Center -> SMI Command -> War Room -> Checkpoints
Date: 2026-09-05

## Master rule

Movement Intelligence and Booking Intelligence must never turn green by wording alone.
A checkpoint may only be green when it has a registered route, a public/private boundary, a Guardian/Aegis safety result, a proof state, and a safe next gate.

Anything that affects people, money, travel, location, suppliers, reservations, or real-world dispatch remains Human Authority gated.

## Placement

```text
SMI Command
└── War Room
    ├── Movement / Map Control
    │   ├── Route proof
    │   ├── Movement booking request
    │   ├── Match proposal
    │   ├── Tracking consent
    │   ├── Payment-intent boundary
    │   ├── Link Up trip binding
    │   ├── HRM movement receipt
    │   └── Green Gate status
    └── Booking / Travel Supply Control
        ├── OAP Direct catalogue
        ├── Quote check
        ├── Buyer hold
        ├── Reservation request
        ├── Founder supply control
        ├── Supplier certification
        ├── Inventory / availability
        ├── Supplier confirmation
        ├── HRM booking receipt
        └── Green Gate status
```

## Current direct checkpoint routes

```text
/mission/checkpoints
/mission/checkpoints/movement-intelligence
/mission/checkpoints/booking-intelligence
/mission/war-room/checkpoints
/mission/war-room/checkpoints/movement-intelligence
/mission/war-room/checkpoints/booking-intelligence
```

These routes are Founder/private Mission Control checkpoints. They must not dispatch, reserve, charge, approve, migrate, or expose private operational data.

## Movement Intelligence gap closure

### Green / implemented software boundaries

- Public Movement surface route exists: `/movement`.
- Public Movement status route exists: `/movement/status`.
- Private Movement workspace route exists: `/movement/workspace`.
- Private route planning endpoint exists: `/movement/route`.
- Authenticated movement booking request endpoint exists: `/movement/bookings`.
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
- Movement schema proof is needed before booking/match/tracking records are certified.
- HRM movement receipt proof is needed for important movement decisions.
- Green Gate automation must read real Movement checkpoint results.
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

## Booking Intelligence gap closure

### Green / implemented software boundaries

- Public Travel surface route exists: `/travel`.
- Public OAP Direct route exists: `/travel/direct`.
- Public catalogue API exists: `/travel/api/catalogue`.
- Public direct offers API exists: `/travel/direct/api/offers`.
- Public quote endpoint exists: `/travel/direct/api/quote`.
- Authenticated buyer hold endpoint exists: `/travel/direct/api/hold`.
- Authenticated buyer reservation request endpoint exists: `/travel/direct/api/reservations`.
- Founder supply dashboard exists: `/mission/supply`.
- Founder supply status API exists: `/mission/supply/status`.
- Supplier creation/review/certification endpoints exist under `/mission/supply/suppliers`.
- Listing creation/photo/activation endpoints exist under `/mission/supply/listings`.
- Inventory endpoint exists: `/mission/supply/inventory`.
- Supplier reservation confirmation endpoint exists: `/mission/supply/reservations/confirm`.
- Partner Supply status/import routes intentionally return removed/blocked state.

### Booking gaps now marked as proof-needed, not missing architecture

- OAP Direct supplier record must be certified by Founder.
- Commercial terms must be certified before public supply is treated as ready.
- Active listing and photo safety proof must exist.
- Availability/inventory proof must exist.
- Buyer hold proof must exist with CSRF and authenticated identity.
- Reservation lifecycle proof must exist from request to supplier confirmation.
- HRM booking receipt proof must record quote/hold/reservation/confirmation decisions.
- Green Gate automation must read the real Booking checkpoint state.
- Public claims must remain conservative until supplier and reservation proof exist.

### Booking locked items

- External marketplace import is blocked.
- External provider authority is false.
- Payment capture is locked.
- Confirmed reservation claim is locked until supplier confirmation proof exists.
- Commission/revenue claim is locked until commercial receipt exists.
- Refund/cancellation handling must be proven before money flow is certified.
- Any accommodation, travel, ticket or event supply must be direct, certified, and auditable.

## Shared Green Gate rule

A Movement or Booking checkpoint can only show green when all of the following are true:

1. Route exists.
2. Access boundary is correct.
3. Button/endpoint performs a real safe action or returns a clear locked state.
4. Data source/store exists.
5. Failure is safe.
6. Guardian/Aegis blocks unsafe use.
7. HRM receipt exists for consequential action.
8. Public claim is accurate and not over-stated.
9. Human Authority approves consequential real-world movement, money, reservation, supplier, or public claim.

## Final truth board

```text
Movement architecture:          GREEN
Movement route/checkpoint URLs: GREEN
Movement private boundary:      GUARDED
Movement live route proof:      BUILDING
Movement schema proof:          BUILDING until status is proven
Movement real dispatch:         LOCKED
Movement payment capture:       LOCKED
Movement hidden tracking:       BLOCKED

Booking architecture:           GREEN
Booking route/checkpoint URLs:  GREEN
OAP Direct policy:              GUARDED
Booking supply proof:           BUILDING until certified supplier/listing/inventory exists
Booking reservation lifecycle:  BUILDING until confirmed receipt exists
Booking external import:        BLOCKED
Booking payment capture:        LOCKED
Booking public confirmed claim: LOCKED until proof
```

## War Room decision

These systems are now considered structurally complete for safe software checkpointing.
They are not considered fully operationally certified until live route results, schemas, HRM receipts, supplier/inventory evidence, and Green Gate automation are proven.

No fake green.
No hidden tracking.
No unsafe dispatch.
No third-party booking authority.
No payment capture without compliance proof.
No confirmed reservation claim without supplier confirmation proof.
