# The Spot scope

This change is presentation and truthfulness hardening for the public Spot front door.

Included:
- postcode-first visitor context;
- compact priority cards;
- simple visitor-facing state labels;
- preservation of all canonical Spot capability links;
- explicit public/private boundary copy;
- regression contracts for the front door.

Not activated by this change:
- checkout or payments;
- driver/courier dispatch;
- carrier activation;
- live tracking;
- merchant or creator verification;
- private LinkUp access;
- Founder/private dashboard access;
- production turn-by-turn routing;
- OAP-owned weather observation.

Those functions remain governed by their existing runtime, identity, safety, provider, and Human Authority gates.
