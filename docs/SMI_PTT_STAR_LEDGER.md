# SMI PTT mission — evidence star ledger

Status: proposed, review-only; no autonomous agent votes or production readiness implied.

## Governance
- Founder Final controls release. Captain ALL IN is the named scoreboard custodian; SMI is referee.
- Four judging criteria: Shere Khan (reliability), Fox (evidence), Bagheera (risk), Gorilla (security).
- All four criteria must have traceable human-reviewed evidence before a star is awarded. A judge's own contribution requires independent review.
- One verified, distinct completed task earns at most one star for its accountable owner. No stars for plans, simulations, duplicate reports, or passing CI presented as live voice.
- Store evidence references and dates. Reassess a star if proof is invalidated.
- No independent agent activity, voting, or approval is implied by these role names.

## Round 1 — baseline (2026-10-23)
| Task | Responsible role | Evidence | Status | New stars |
| --- | --- | --- | --- | ---: |
| Inspect current PTT readiness | Fox / SMI | `mission_control/ptt_routes.py` returns `live_ready: false`; `static/ptt_live.js` uses `iceServers: []` | Evidence inspected; review not independently signed | 0 |
| CI coverage for live client | Seraph / Neo | PR #1296 proposes `node --check static/ptt_live.js` | Open PR; not merged into main | 0 |
| HOLD/STOP behavioural proof | Neo / Gorilla | Client disables audio tracks on release and stops tracks on close | Automated behavioural proof pending | 0 |
| Secure first-party TURN | Architect / Panther | No verified TURN configuration | Pending | 0 |
| Two-device audio verification | Trinity / Falcon | No physical device receipts | Pending | 0 |
| Founder production release | Founder Final | No live-ready proof | Blocked | 0 |

**Round 1 stars: 0. Cumulative stars in this ledger: 0.**

## Required receipt for each later round
Record: round number, date, scoped task, responsible role, exact commit/test/device evidence, four independent criterion outcomes, referee decision, awarded star (0 or 1), and any unresolved production gates.

## Live-readiness gate
Never mark OAP PTT live-ready solely from signalling, a JavaScript syntax check, or local browser controls. Require authenticated first-party STUN/TURN or justified ICE reachability, two physical devices on separate networks, verified audio transmission, HOLD release and immediate STOP microphone shutdown, plus operational deployment evidence.

## Round 2 — PTT reconnection control (2026-10-23)
| Task | Responsible role | Evidence | Status | New stars |
| --- | --- | --- | --- | ---: |
| Restore Connect button after session close | Neo (implementation role), Fox (investigation role) | Commit `853f6003c3a13463e50cc8177dc673886ede20f3` changes `static/ptt_live.js` | Committed, CI and behavioural proof pending | 0 |

**Round 2 stars: 0. Cumulative stars: 0.** Judges have not issued independent, evidenced approvals. This commit does not establish TURN, two-phone audio or production readiness.

## Round 4 — governed CI completion (2026-10-24)
| Task | Responsible role | Evidence | Status | New stars |
| --- | --- | --- | --- | ---: |
| Governed CI completion | Seraph (CI role), Captain ALL IN (record) | [GitHub Actions run #6778](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40035070429) for commit `0cf49a439972404b8b6b82a779899fab40e89878`: `completed`, `success` | Verified workflow conclusion; four independent judging criteria and PTT behavioural proof pending | 0 |

**Round 4 stars: 0. Cumulative awarded stars: 0.** This workflow success does not certify physical-device audio, HOLD/STOP behaviour or deployment.
