# OAP Radio — Internet First / Greater London FM Readiness

Status: planning and evidence-gated. No stream, FM licence, transmitter, or public broadcast is claimed.

## Mission
OAP-owned station identity, scheduling and original content; internet broadcast first, Greater London FM as long-term licensed objective. Initial FM service area is subject to spectrum availability, community-radio eligibility, engineering and Ofcom approval.

## Existing software boundary
Reuse `mission_control/radio_core.py` and existing owner-scoped `/mission/organs/radio` routes and OAP music interface. Do not create a parallel radio registry or second player. Current radio-core output explicitly reports `broadcast_live: false` and `public_stream_url: null`; scheduling a show does not transmit audio.

## Seven evidence gates
1. Founder approves brand, editorial responsibility and legal applicant; assess community-radio entity eligibility independently.
2. Inspect current radio routes, tests and rights adapters on exact main revision; preserve Founder-only controls.
3. Implement a separately authenticated ingest-to-encoder-to-stream service with limited resources, observability, recovery and disabled-by-default public output; no embedded credentials.
4. Verify OAP World listening UI only against a real, accessible stream endpoint, with stop/failure indicators and no fake LIVE badge.
5. Verify recorded-content, performance, composition, online and FM rights by medium, territory and time; block unlicensed playback.
6. Check official Ofcom expression-of-interest window and submit only with explicit Founder authorisation; independently verify any purported deadline before relying on it. Define London-wide ambition separately from proposed initial technical coverage.
7. FM transmission only after licence, frequency, approved site, compliant equipment, engineering and real on-air acceptance tests.

## Operations
Station / show approval stays Founder-private. Editorial and safeguarding escalation are human-owned. Guardian and HRM retain evidence and audit boundaries. No automatic publication, payment, transmission, frequency assignment or external application. Mark unknown telemetry NOT_CONNECTED. Do not report completion percentages without verified checks.

## Next smallest implementation proof
Run existing `tests/test_radio_core.py` and radio-related route/rights tests on the exact proposed head, then add a focused regression ensuring schedule metadata cannot mark `broadcast_live` true or create a `public_stream_url` without independently verified transport evidence. This document alone does not establish that test proof.
