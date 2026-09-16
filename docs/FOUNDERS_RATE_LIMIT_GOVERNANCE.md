# Founder sign-in rate-limit governance

Founder sign-in must count only genuine credential rejections toward the bounded sign-in window.

- Exact duplicate submissions remain coalesced.
- Infrastructure/provider failures do not consume a Founder sign-in attempt.
- Successful sign-in clears the sign-in failure window.
- Founder activation retains its separate bounded-attempt semantics.
- Client identity remains derived through the trusted SMI gateway path.
- Private access remains fail-closed.

This document records the production invariant; executable enforcement lives in `mission_control/web_security.py` and the sign-in route.
