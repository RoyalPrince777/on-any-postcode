# OAP Lab + Founder entrance — seven-gold-star proof contract

Scope: Founder entrance → Personal SMI Chat → optional Command Centre and OAP Lab.
Human Authority remains final. This document is a code/design acceptance contract, not an operational or deployment status report.

## 3× / 7× / 21×
3: identify task, evidence and boundary.
7: test truth, function, security, stability, integration, compliance and learning.
21: use three checks per star (source/action/result; input/state/output;
identity/authorisation/CSRF; mobile/keyboard/failure; route/script/provenance;
privacy/youth/accessibility; retained result/correction/retest).
These are review lenses inside the existing four quarters; never 21 autonomous agents or new gates.

## Seven-star acceptance, no fake green
1. Truth: no configured flag, illustration or static test is called an operational success.
2. Function: the password → SMI → Plus → Upload/Stop → result journey is exercised.
3. Security: anonymous Lab/asset endpoints fail closed; CSRF, lockout and safe-next are preserved.
4. Stability: real narrow screen, mobile keyboard, missing artwork and error/reload cases are checked.
5. Integration: one valid rendered HTML document; CSS is inside head, scripts in body; canonical control owner and working links.
6. Compliance: human-centred accessibility, first-party privacy, youth protection and no deceptive capability claims.
7. Learning: exact revision, reproducible evidence, failed cases and corrections are retained.

The seven-star tests in tests/test_oap_lab_seven_star.py cover bounded repository
and Flask-rendering evidence; tests/browser_founder_e2e.py drives real Chromium
against LOCAL test-only identity and stream fixtures, not the real Founder
password, real SMI provider, or a physical Android device. Do not award gold for
this document, an unrun workflow, or a passing code/browser test alone.

## Evidence from 20 September 2026 (controlled environment)
- CI #35500974050, exact head 492ca1f438fc17b92f3830c272cadb673a29c165:
  both jobs SUCCESS; 1,518 Python tests; Node async-attachment and Stop
  replacement-race tests PASS; Chromium Founder flow, narrow viewport, and
  CSRF/ten-attempt lockout PASS.
- Chromium used the actual Flask forms/routes, private Lab, Plus picker and
  browser streaming UI, with local-only authentication and provider fixtures.
- The executable lockout test exposed a genuine Flask parsed-form fingerprint
  defect: distinct wrong passwords coalesced and never reached 429. Fixed in
  mission_control/web_security.py by digesting parsed form fields without
  retaining/logging the passwords; both form regression and Chromium retest pass.
- No third-party browser resource requests were observed in the fixture run;
  browser keyboard Plus/ESC, chat-first reload and narrow viewport passed.
- Full-experience gold remains 2/7: Truth and Learning. Function, Security,
  Stability, Integration and Compliance have stronger test evidence, but the
  separate real-account/provider/physical-device/manual checks and Founder
  final decision have not been proven here. Do not call them green by proxy.

## Placement
OAP Lab is a private Founder workspace containing Research, Matrix/War Room,
Build & Verify, and existing Founder asset metadata. Human Lab is a proposed
division, not a claimed clinical or production capability. No eighth
Intelligence World, second SMI brain, additional ledger or new approval owner.
The Command Centre is optional; chat is the default working surface.
