# Durable journey ownership and cancellation

This candidate combines existing PRs #1261 (Eats), #1201 (journey contract),
#1205 (Ride), #1262 (routing), #1265 (host), #1271 (SMI truth mode) and #1256
(mission protocol). They remain draft engineering work, not a deployed release.

## One engine, durable identity

The existing Movement create-booking operation now mints a server-side journey
UUID and persists its association inside the booking transaction. Both owned
records must agree with an active canonical identity. Same-key retries preserve
one booking and one journey; a failed product binding rolls both back.

`GET /movement/journeys/<journey_id>` and the existing booking read require the
persisted owner. `GET /eats/orders/<order_id>/delivery` reads order, booking,
journey ownership and cancellation receipt in one SQL snapshot. Merchant order
read rights do not grant this customer-only delivery access. Caller-supplied
owner, actor, journey ID or product-authority claims are not accepted by writes.

New journey IDs are minted by the server. Existing in-memory Ride UUIDs and
Booking Core intents are not silently adopted; their durable ownership remains
unverified. Existing booking IDs remain owned by Movement. Legacy bookings may
have no association on read; reads never create one.

## Atomic digital cancellation

Eats customer/merchant cancellation uses its persisted role and graph gates,
then cancels the Movement booking in the same transaction. Product-bound
bookings cannot bypass that gate through the generic Movement cancel endpoint.
Unbound bookings use `POST /movement/bookings/<booking_id>/cancel` with session,
CSRF and rate-limit guards. In-progress/completed bookings cannot be cancelled
by this path. An identical cancellation has one receipt and no duplicate order
event. A cancelled order cannot create a fresh delivery.

The existing order graph is preserved: `authorised -> cancelled` is not an
allowed edge. Positive product-cancellation proofs start with confirmed orders;
this path does not widen cancellation authority or invent financial transitions.

Cancellation expires proposed/accepted match records, revokes tracking consent,
closes the trip channel and cancels pending internal connectivity/payment drafts.
An assigned worker is set OFFLINE rather than automatically made available;
another active assignment preserves BUSY. Historical records are retained.
Match acceptance, decline and cancellation lock the booking before proposals.
Acceptance also locks the worker identity to prevent simultaneous assignments
across different roles. These are application-path invariants, not a substitute
for external operator or vehicle evidence.

Canonical SIKA intents and holds are preserved. No refund, release, settlement,
external cancellation notice or courier dispatch is performed. The delivery
readback flags payment action required for cancelled orders with bound payments.

## Migration and recovery proof

Apply the existing opt-in global journey association migration and the separate
`0002_oap_journey_cancellation_receipts` migration before compatible writers.
The original Movement and association schema checksums remain unchanged.
Initialization is explicit and checksum-governed; imports/status reads never
migrate production. No production migration is part of this work.

Isolated loopback PostgreSQL cases cover committed readback, foreign owners,
unverified intents, retries, competing creates/cancels/matches and transactional
failure. Test subprocesses are actually killed with SIGKILL immediately before
or after PostgreSQL commit, then a fresh process/connection retries the request.
This proves bounded application-process recovery, not database/server power-loss
durability, physical delivery, live dispatch or payment execution.

The combined CI retains real Eats/PostgreSQL verification and the separate
blocking routing-readiness job. Its unrelated third-party weather observation
was removed from this software workflow; this does not change weather runtime
implementation or claim an owned observation network. Local browser fixtures,
host declarations, credentials and containers do not certify a live host.

Courier and Quick product surfaces, merchant/operator onboarding, controlled
routing infrastructure and live end-to-end acceptance remain separate gaps.
Overall and component product VPI remain N/A.
