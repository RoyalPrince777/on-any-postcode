# Founder failed-password guard

This change makes the Founder sign-in lockout count only completed 401 credential rejections.

- 401 wrong credentials count toward the bounded five-minute window.
- Exact duplicate submissions inside the duplicate window coalesce.
- 400/403/5xx sign-in responses release the reserved slot.
- A successful sign-in clears the key through the existing application flow.
- Activation retains its existing policy: only 5xx responses release its reserved slot.
- Trusted client-key derivation remains unchanged.

Production must not be marked green until governed CI and live verification pass.
