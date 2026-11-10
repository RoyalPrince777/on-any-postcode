# OAP Black History Intelligence — first-party integration contract

**Decision scope:** Founder-directed research and design review, 26 October 2026. **Status:** proposed contract / NOT implemented / no Green claim.

## One brain, existing doors
SMI coordinates cultural research and source verification. This is **not** an independent agent, passport, system of historical authority or new top-level app. Reuse:
- **OAP World** for geographical discovery, with opt-in regional context.
- **Chronicle** for dated sourced historical entries and timelines.
- **OAP Library** (`/library/books`) for first-party catalogued publications where rights/entitlements permit.
- **My World** for optional personal reading and saved research; never infer racial identity or ancestry.
- **OAP Data / Guardian** for provenance, sensitive-data boundaries and correction history.

The names above are integration targets, not claims that this feature or those joins currently run in production.

## Content tracks (starting topics; NOT accepted factual claims)
1. Ancient and medieval African societies and intellectual traditions.
2. Akan, Akyem, Begoro, KORADASO: distinguish independently documented history from personal/family oral traditions.
3. Black Britain and the South London diaspora, including migration and local community histories.
4. Atlantic slave trade, enslavement, resistance and abolition, with survivor-centred documentation.
5. African and Caribbean independence movements and civic history.
6. Black science, enterprise, arts, food, language and sport.
7. Contemporary global Black experiences, with location- and time-specific sourcing.

## Minimum content record (proposal)
- `entry_id` (stable ID); `title`; `topic_tracks`; `summary`
- `place` including geolocation **only** for independently evidenced public historical places; no invented coordinates
- `period_start`, `period_end`, `date_precision`, `date_uncertainty` (allow approximate/unknown)
- `sources[]`: publisher/holder, URL or archival reference, publication/access date, relevant pages
- `claim_status`: sourced / disputed / oral-history / awaiting-verification (default: awaiting-verification)
- `perspectives[]`, `editorial_review`, `correction_log`, `last_reviewed_at`
- `rights`: text/media permission, restrictions, creator credit; no automatic reuse of protected material
- `sensitivity`: public / access-restricted; identity and descendants' data excluded by default

## Display rules
- Explain a claim's evidence and uncertainty in everyday English, allow Twi and South London linguistic presentation **without changing factual meaning**.
- Show source links and avoid manufactured dates, places, quotations, depictions or certainty.
- Distinguish archival facts, scholarly interpretations, folklore and family oral histories; oral testimony requires permission.
- No automatic identity classification, ancestry inference, public family tree, surveillance or covert collection.
- No political endorsement; contested topics need time/place context and attributable perspectives.
- Sensitive/restricted material cannot enter public maps, feeds, external search indexes or automated recommendations by default.

## Smallest legitimate first slice
1. Audit existing OAP World, Chronicle and Library models/routes to locate safe extension points.
2. Add **read-only**, off-by-default catalogue support for independently verified, rights-cleared records.
3. Add unit tests for incomplete source references, chronology uncertainty, conflicting interpretations, access restrictions, missing media rights and no fabricated geolocations.
4. Verify authenticated, accessible user navigation on the actual first-party runtime, including source view, correction/withdrawal and failed-record behaviour.
5. Require independent security/content review and human Founder Final before enabling. No Render, no placeholder demo treated as success.

## Acceptance conditions
The feature is not Green based on this document, a proposed JSON example, mock fixtures, or an image. Require committed implementation, passing exact-head CI, original-source verification for published entries, permission and copyright review, and real first-party runtime acceptance. Existing agent IDs, governance and OAP terms remain unchanged.
