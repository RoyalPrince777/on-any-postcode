# OAP Data — first-party only; no Meta integration

Founder direction: OAP Data is a first-party ON ANY POSTCODE service. Do not add, configure, or reactivate Meta Platforms integrations as OAP Data processors, transport, authentication, analytics, advertising, tracking, or profile enrichment. This includes Facebook/Instagram/WhatsApp SDKs and APIs, Meta Pixel, conversion APIs, and automatic data sharing. No Meta cookies, tracking IDs, or external scripts in the first-party OAP Data entry surfaces.

This rule does **not** require deleting ordinary technical metadata or erasing user-owned content that happens to mention Meta products. Do not silently delete user data. External social links in unrelated editorial content must be evaluated separately and must never become invisible OAP Data transfers.

The current small regression test checks app.py, templates/home.html and templates/world.html for known tracker/API signatures. It does not scan all modules, all database records, third-party infrastructure or production HTTP traffic. Release proof requires a broader dependency and runtime network audit, checking consent, cookies, account integrations, request logs, data retention and previously collected data. Historical transfers cannot be undone by changing repository source.

Removal of any live credentials, webhooks, user consent settings or historical data requires an inventoried, reversible change and applicable deletion/privacy controls. Preserve Founder Final, HRM attribution and existing first-party data access boundaries.

Acceptance: no Meta-owned data processors or automatic outbound requests in OAP Data; no hidden trackers; tests and runtime network evidence; explicit human decision on any retained unrelated social links.
