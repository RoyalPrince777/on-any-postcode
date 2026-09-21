# Personal SMI — Founder chat / War Room continuity bridge (draft)

Status: design and bounded chat-routing implementation; not a deployment or runtime certification.
Scope: authenticated Personal SMI only. OAP Studio Intelligence stays public/private isolated.

## Intent
Bring the way the Founder works in this chat to the existing Personal SMI chat runtime.
Short commands continue the currently supplied conversation-owned mission; they do
not grant tools, system authority, payment power, code merge/deployment or Green Gate.

## Canonical protocol (reuse existing sources rather than duplicate engines)
- One SMI Brain; NEXUS nervous system; HRM/JOOG governed memory and Chronicle evidence.
- Modes: AUTO smallest sufficient 3/7/21; Manual 3/7/21; explicit War Room 21.
- Seven councils: Civic, Jungle Book, Animal, Matrix, Civilisation, Akan Core, Akan Animal.
- Seven default judge seats: Shere Khan, Bagheera, Agent Smith, Lion, Morpheus, Akela, Owl.
- Guardian and Green Gate are separate judges/gates; Neo is recovery witness.
- Registered review agents selected by task and evidence; rule-lens simulations
  must never be represented as independent agent executions.
- Existing 26 lenses from intelligence_lenses.FULL_LENS_IDS.
- Seven passes: Discovery, Verification, Alternatives, Adversarial, Systems,
  Consequence, Synthesis. Accumulate evidence and dissent, do not repeat seven answers.
- Seven stars: Truth, Function, Security, Stability, Integration, Compliance, Learning.
- Vote board: attributed PASS, FAIL or ABSTAIN/CONDITIONAL; include minority report.
- End Review: Neo -> Shere Khan -> Bagheera -> Agent Smith -> Judges -> SMI Return
  -> Green Gate; Founder Final remains separate.

## Short-command contract
- Purple / continue: continue the current mission only if supplied owned conversation
  or governed memory actually supports a subject; otherwise report unavailable context.
- Green: approval of the explicit current design or quarter only, not a signed action
  receipt, automatically executed operation or production-green certification.
- Jog memory: use only authenticated conversation and governed HRM/JOOG records.
- STOP: use actual cancellation, not a text-only assertion of a stopped runtime.
- War Room / SMI 21: select depth 21 when the selector is AUTO; explicit Manual wins.
- The four build stages are separate: 25% Rollback/Recovery; 50% Runtime Guard;
  75% Aegis Isolation/Recovery; 100% Green Gate + Founder Final.
- KEEP / UPGRADE / MERGE / REMOVE; no middlemen, no third-party telemetry in OAP;
  no fake green and no second SMI brain.

## Founder view
Keep the chat low-noise: MISSION / MODE / ALIGNMENT / PROTOCOL / DONE / LOCKED / NEXT.
Detailed results may expose evidence, seven councils, judge findings and counterviews,
agreed/disagreed/unresolved, strongest/weakest link, stars, vote percentages, dissent,
Guardian/Aegis, Green Gate, the actual receipt and Founder Final. Do not invent votes,
tool results, persisted records or completion percentages.

## What is actually implemented in this branch
One pure, side-effect-free private Founder turn resolver, fed into the existing
chat brain metadata and local/bridge/compatibility inference context. It preserves
the original message, supplied history, approval boundary and Manual selector.
New tests cover short directives, context absence, judge/lens canonical sources,
mode boundaries and public/private routing.

## Still open and not certified
The supplied chat history is bounded; cross-chat automatic memory recall, long
mission replay, native review-board vote persistence, verified specialist-agent runs,
genuine chat tool invocation, plus/tools drawer, exact-action approvals, durable
War Room receipts and production UI parity require their own runtime tests.
Do not treat this prompt/context bridge as those implementations.

## War Room gate
25% is pending branch/CI review and recovery proof; 50%, 75%, 100% remain unproven.
Draft only, no merge, deploy or A6/A7 enablement.
