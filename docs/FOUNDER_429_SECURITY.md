# Founder 429 security invariants

Any eventual fix must preserve all of the following:

- Founder private surfaces remain Founder-only and fail-closed.
- Anonymous profile creation remains unavailable.
- Recovery credentials remain server-validated and are never logged by diagnostics.
- CSRF/session protections remain intact.
- No global removal of rate limiting.
- Any exemption must be narrowly scoped, evidence-backed, and auditable.
