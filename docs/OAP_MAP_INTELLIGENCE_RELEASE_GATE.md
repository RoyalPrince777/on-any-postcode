# Map Intelligence release gate

This change may merge only when repository checks prove the single-surface contract.

Required:

1. `Map Intelligence` is the only public capability for maps, routes, weather, travel, movement, OAP Direct/booking and delivery.
2. `movement-delivery` is absent from the public capability registry.
3. Governed Movement backend endpoints are not removed merely because the public UI is consolidated.
4. No new payment, dispatch, tracking or confirmed-booking claim is enabled.
5. Regression tests pass in CI.
6. Production deployment is a separate Human Authority gate.

Founder recovery / PR #217 is outside this change and must remain a separate workstream.
