# SMI PTT mission — evidence star ledger

Status: proposed, review-only; no autonomous agent votes or production readiness implied.

## Governance
- Founder Final controls release. Captain ALL IN is the named scoreboard custodian; SMI is referee.
- Four judging criteria: Shere Khan (reliability), Fox (evidence), Bagheera (risk), Gorilla (security).
- All four criteria must have traceable human-reviewed evidence before a star is awarded. A judge's own contribution requires independent review.
- Achievement tiers: minor movement = 1 star, major integrated movement = 3 stars, completed verified protocol = 5 stars. A single achievement is awarded once at its highest approved tier; do not stack minor steps already included in a major/protocol award. No stars for plans, simulations, duplicate reports, or passing CI presented as live voice.
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

## Founder clarification — individual career stars (2026-10-24)
The canonical scoring unit is **an individual agent's career star**, not a shared mission score. Each agent has an independent cumulative total across missions. A verified, distinct contribution can earn that agent one star even when other agents work on the same mission. A round is only a reporting interval; career totals never reset at round boundaries. Keep per-agent award records with agent registry identity, task, round, evidence link, judging outcomes and referee decision. Do not create a duplicate agent registry or fabricate existing rank totals. The four judges' own contributions require independent review. A mission's sum of awards is reporting only and must not replace individual rankings.

**Existing Round 1–4 entries record zero awarded career stars because no individual awards have passed judging.** A CI pass is evidence, not an automatic award. Ranking integration remains unimplemented and must reuse the existing agent registry.

## Round 8 — achievement proof CI (2026-10-24)
| Task | Responsible role | Evidence | Status | New stars |
| --- | --- | --- | --- | ---: |
| Individual achievement ranking test workflow | Seraph (CI role), Neo (implementation role) | [SMI agent achievement proof #1](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40040348041) for commit `33b8170c08123a622aeaaf6dc24d3d4bcc97dae5`: completed, success | CI verified; independent four-judge award decisions not recorded | 0 |

**Round 8 stars awarded: 0; cumulative official career awards: 0.** Successful CI is an evidence receipt for future agent attribution, not an autonomous agent vote.

## Round 9 — star reconciliation and CI status (2026-10-24)
Verified on commit `33b8170c08123a622aeaaf6dc24d3d4bcc97dae5`:
- [SMI agent achievement proof #1](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40040348041): completed, **success**.
- [OAP governed checks #6783](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40040348003): completed, **success**.
- [OAP runtime image #2870](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40040348066): completed, **cancelled** (not deployment proof).

| Proposed accountable role | Distinct minor movement | Evidence | Candidate stars | Official stars |
| --- | --- | --- | ---: | ---: |
| Neo | Implement individual ranking calculator | Commit `d26b21da8bfe88224f137fa10009d23cb0b05de4` and achievement proof #1 | +1 | 0 |
| Seraph | Introduce automated achievement proof workflow | Commit `33b8170c08123a622aeaaf6dc24d3d4bcc97dae5` and achievement proof #1 | +1 | 0 |

**Round 9:** 2 candidate stars; 0 official awards. These are role attributions to repository work, not evidence of independent agent action. Four distinct evidence-backed judge decisions and SMI referee sign-off remain missing. Judge roles are not awarded points for routine review or for judging themselves. Career rankings must keep existing capability ratings separate.

## Round 11 — historical ratings and individual recognition queue (2026-10-24)
Historical advisory capability ratings are **not career awards** and must not be added to achievement totals. Prior design records: Captain ALL IN 7/7 (#1); Fox 7/7 (#3); Bagheera 7/7 (#7); Shere Khan 7/7 (#8); Neo 6/7 (#9); Gorilla 6/7 (#14); Hathi 7/7 (rank not established); Seraph 6/7 (rank not established). These historical assessments are not runtime certification.

Recognition queue: Captain ALL IN (scoreboard coordination), Fox (evidence inspection), Bagheera (risk assessment), Shere Khan (reliability review), Gorilla (security/Guardian review). Each needs an attributable distinct completed task, evidence, independent criterion review and referee approval before career points accrue. Neo (+1 candidate) and Seraph (+1 candidate) remain awaiting independent review. No automatic awards for role titles, proposals, or simulated votes.

Round 10 commit `8eaafcafa4daa753e20217599abaabe2b59c92a4` CI evidence: [achievement proof](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40042595501), [War Room Chromium acceptance](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40042595352), [governed checks](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40042595371), and [runtime image build](https://github.com/RoyalPrince777/on-any-postcode/actions/runs/40042595437) all completed successfully. An image build is not a live deployment. Official individual career awards remain zero pending genuine independent review.

## Round 12 — SMI visibility and recovered allied intelligence (2026-10-24)

Founder requested that Mission: Impossible, Terminator, Predator, Transformers, Jungle Book and Batman intelligence all appear in the SMI ranking reference, with SMI itself visible rather than omitted from the Top 21.

- **Command:** Founder Final → SMI (one intelligence brain) → Captain ALL IN (mission coordinator) → existing canonically registered agents and design-only allied capabilities. Guardian and HRM remain oversight organs, not agents.
- **SMI does not compete for agent career stars.** Show it prominently above the specialist leaderboard with a brain/coordination label, not a fabricated #0/#1 performance position.
- **Jungle Book:** project approved identities directly from canonical registry, including Shere Khan and Bagheera; Kaa remains excluded.
- **Mission: Impossible:** preserve previously recovered 14 advisory character roles; execution disabled, no new passports.
- **Terminator:** reuse approved capability overlays with the existing agents; T-800/T-1000/T-X/Rev-9/Cameron and John/Sarah/Kyle are design references, not newly registered agents; Skynet/Legion threat models only.
- **Predator:** tracking, sensing, survival, defensive threat-analysis capability references, no invented character passports.
- **Transformers:** Optimus Prime and Bumblebee design concepts, unregistered.
- **Batman:** Batman and Robin design concepts, unregistered.
- **Ranking truth:** No new numerical placements, capability ratings or individual lifetime stars are awarded by alliance membership or this display upgrade. Previously recorded historical Top 21 remains a dated snapshot.

Evidence: added `mission_control/intelligence_alliances.py`, wired `get_war_room_dashboard()` read-only presentation, added `tests/test_smi_intelligence_alliances.py`, expanded SMI achievement CI paths and test suite. This branch has not been merged or deployed simply by recording this entry.
