# SMI Thinking Process Runtime Certification v1

The certification endpoint proves the deployed observable Thinking Process through the signed private SMI gateway without creating a Founder session, calling an inference provider, writing HRM, or exposing private chain-of-thought.

Certified runtime stages:

1. Understand
2. Context
3. Route
4. Evidence
5. Challenge
6. Synthesise
7. Govern

The probe validates stage order, canonical stage count, safe public stage events, redundant SMI-prefix cleanup, coherence of a safe response, rejection of private-reasoning disclosure, no decision authority, no execution authority, and Human Authority final.

Production boundary:

- Public origin: `/api/smi/thinking-certification` is private and fail-closed.
- Private SMI gateway: only the exact certification path is proxied with the configured signed gateway credential.
- The certification performs no provider call and no HRM write.
- The certification does not replace Founder authentication and does not bypass Founder-only dashboard access.
