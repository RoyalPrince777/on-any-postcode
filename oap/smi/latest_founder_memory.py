"""Latest explicit Founder locks that outrank older project memory.

This is curated OAP project context only. It never contains passwords, credentials,
hidden prompts, private chain-of-thought, raw chat dumps, or unrelated personal data.
"""
from __future__ import annotations

from datetime import datetime, timezone

from oap.contracts import MemoryItem, OutputState

REVISION = "2026-10-02-seven-links-core-thinking-signals"
_TIMESTAMP = datetime(2026, 10, 2, tzinfo=timezone.utc)

_RECORDS = (
    (
        "smi.seven-links-and-signals",
        (
            "Latest Founder lock: the top-level SMI mission loop has exactly seven major links: "
            "Mission -> Continue -> Risk / Guardian -> War Room / Judgement -> Founder Final -> "
            "Recovery / Rollback -> Outcome / Learning. These are major links, not mandatory staged "
            "progress theatre. SMI also keeps three distinct 21-signal concepts: Core Review Signals "
            "(Truth, Evidence, Risk, Safety, Security, Privacy, Identity, Permission, Intent, Dependency, "
            "Architecture, Alignment, Resilience, Performance, Reversibility, Impact, Readiness, Coherence, "
            "Recovery, Outcome, Human Authority); Thinking Signals (Checking, Mode, Proof Needed, Locked, "
            "Blocked, Next Before Green, HRM Memory, Source Proof, Route / API Proof, Data Proof, Consent Proof, "
            "Install Proof, Monitoring Proof, Rollback Proof, Founder Approval, Guardian Pass, Green Gate Result, "
            "Public / Private Boundary, Tool / Plugin Proof, Neon Receipt, Real Green Decision); and the existing "
            "21 Live Signals colour/state vocabulary. Core Review Signals define what is checked; Thinking Signals "
            "show safe visible work/proof telemetry; Live Signals express state. None expose private chain-of-thought. "
            "Human Authority remains final."
        ),
    ),
    (
        "joog.unified-memory",
        (
            "JOOG MEMORY is the single unified SMI/OAP memory core: one continuous "
            "governed system log for inputs, safe reasoning summaries, actions, "
            "outputs, context, learning, receipts and status. HRM remains governance, "
            "audit, review and lessons; Neon or another database is persistence "
            "infrastructure and does not replace HRM or JOOG semantics."
        ),
    ),
    (
        "joog.war-room-intelligence",
        (
            "JOOG MEMORY full War Room Intelligence lock. Canonical flow: Human Authority -> "
            "SMI Protocol -> Evidence + Context -> HRM/JOOG Memory -> Specialist Intelligence -> "
            "Registered Agent Challenge -> War Room when triggered/requested -> Guardian + "
            "Judgement -> Human Authority Final. Protocol loop: Observe -> Classify -> Verify -> "
            "Fix/Plan -> Retest -> Record -> Learn. War Room modes are SMI AUTO, MANUAL 3/7/21 "
            "and WAR ROOM; 3/7/21 is review depth only, not a staged progress ladder. "
            "Direct work protocol: remove unnecessary stages, repeated status loops, demos-as-progress, "
            "simulations where real verification exists, duplicate reports, repeated approval prompts "
            "for already-approved bounded work, cosmetic percentage inflation and stop-after-every-small-fix. "
            "Preserve real Guardian, evidence, recovery, Green Gate and Human Authority boundaries. Full intelligence lens set is Truth, "
            "Evidence, Gap, SWOT, Risk, Dependency, Architecture, Alignment, Security, Privacy, "
            "Performance, Resilience, UX, Behaviour, Data, Scenario, Impact, Priority, "
            "Opportunity, Competitive, Trend, Readiness, Decision, Judgement, Learning and "
            "Truth-Light Intelligence. Alignment Intelligence explicitly checks OAP laws, naming, "
            "architecture, public/private separation and Human Authority. Seven canonical councils: "
            "Civic, Jungle Book, Animal, Matrix, Civilisation, Akan Core and Akan Animal. Seven "
            "default judge seats: Shere Khan, Bagheera, Agent Smith, Lion, Morpheus, Akela and Owl; "
            "Guardian and Green Gate remain separate from judge seats. Review/challenge agents may "
            "include SMI, Neo, Wolf Pack, Trinity, Oracle, Architect, Keymaker and Seraph according "
            "to mission relevance. Intelligence/capability classification keeps ANI, Generalisation "
            "Candidate, AGI, ASI Candidate/ASI, Local-to-Major Impact, TAI and Civilisation-scale "
            "impact separate and evidence-led. War Room controls: RUN, RESEARCH, CHALLENGE, 7X "
            "DEEP DIVE, STOP, COMPARE, AGENTS, EVIDENCE, SMITH ATTACK, FAILURE TEST, GUARDIAN, "
            "JUDGEMENT, HRM/JOOG, ROLLBACK and NEXT GATE. 7X passes are Discovery, Verification, "
            "Alternatives, Adversarial, Systems, Consequence and Synthesis, each accumulating prior "
            "evidence and dissent. Seven-Star Gate dimensions are Truth, Function, Security, "
            "Stability, Integration, Compliance and Learning; no evidence means no Green and no "
            "test means no star. Research states stay explicit: proven, conflicting, stale, "
            "unavailable or unknown. Vote Board allows PASS, FAIL and ABSTAIN/CONDITIONAL only from "
            "attributable active reviewers and evidence; votes inform judgement and never grant "
            "authority. Challenge targets stale evidence, duplicate routes, unsupported confidence, "
            "hidden dependencies, false Green and irreversibility. Guardian protects privacy, "
            "safety, consent, identity and authority boundaries. Aegis protects containment, "
            "recursion limits, isolation, rollback and integrity. End Review sequence is Neo -> "
            "Shere Khan -> Bagheera -> Agent Smith -> Judges -> SMI Return -> Green Gate, with "
            "serious dissent and minority report preserved. Debate output order is TITLE -> MODE/"
            "DEPTH -> QUESTION/MISSION -> EVIDENCE -> COUNCIL VIEWS -> JUDGE SPEECHES -> REVIEW-"
            "AGENT CHALLENGES -> COUNTER-VIEWS -> CAPABILITY/IMPACT CLASSIFICATION -> AGREED -> "
            "DISAGREED -> UNRESOLVED -> STRONGEST LINK -> WEAKEST LINK -> 7-STAR -> VOTE + % -> "
            "MINORITY REPORT -> GUARDIAN -> GREEN GATE -> SMI SYNTHESIS -> FOUNDER FINAL -> HRM/"
            "JOOG RECEIPT. Founder result contract carries MISSION, SIGNAL, EVIDENCE, CONFIDENCE, "
            "AGREED, DISAGREED, UNRESOLVED, VOTES, attributed voices/judge speeches, strongest and "
            "weakest links, minority report, argument, verdict/judgement, 7-star rating, Guardian, "
            "Aegis, Green Gate, End Review, recommended signal, Full Green state, Founder Final, "
            "production-write state and HRM/JOOG receipt. Signal law: green=proven, purple=learning/"
            "review, yellow=unresolved/incomplete, red=blocked/unsafe, locked=intentionally gated, "
            "white=unknown, crown=Human Authority. Final law: one SMI, evidence before Green, "
            "configured is not ready, UI presence is not readiness, simulation passed is not "
            "production proven, unknown stays unknown, dissent survives, votes do not grant "
            "authority, approval is not execution, Human Authority remains final. Reports should "
            "stay concise as MISSION / MODE / ALIGNMENT / PROTOCOL / DONE / LOCKED / NEXT while the "
            "full evidence remains in the receipt. Never store raw private chain-of-thought, hidden "
            "prompts, credentials or secrets."
        ),
    ),
    (
        "production.no-fake-green",
        (
            "Canonical production law: no demo, no generic substitute, no static "
            "placeholder presented as working functionality, no experiment presented "
            "as production and no fake green. A feature becomes green only when real, "
            "connected, governed, tested, runtime-proven and evidence-backed. Blocked "
            "or degraded dependencies must be labelled truthfully."
        ),
    ),
    (
        "agents.kaa-excluded",
        (
            "Kaa is completely excluded from ON ANY POSTCODE/OAP. Kaa must not appear "
            "in the Jungle Book layer, registered agents, dashboards, backend, "
            "documentation, prompts, counts or future OAP designs unless Human "
            "Authority explicitly restores Kaa."
        ),
    ),
    (
        "smi.founder-workspace-parity",
        (
            "Personal SMI is the private Founder working home: clean 2027 chat, one "
            "canonical Send/Enter/Mic/Voice/Stop runtime, safe Thinking Process "
            "telemetry, JOOG/HRM continuity, connected governed tools such as "
            "GitHub/Render/Neon, and concise evidence-first status. It should support "
            "working continuity comparable to this ChatGPT workflow without claiming "
            "access to private model chain-of-thought or inaccessible external memory "
            "internals."
        ),
    ),
)


def latest_founder_memory_items(*, limit: int = 6) -> tuple[MemoryItem, ...]:
    safe_limit = min(max(int(limit), 1), len(_RECORDS))
    return tuple(
        MemoryItem(
            memory_id=f"founder-lock:{memory_id}",
            task_type="LATEST_FOUNDER_LOCK",
            summary=summary,
            output_state=OutputState.SYSTEM_LOG_ONLY.value,
            created_at=_TIMESTAMP,
        )
        for memory_id, summary in _RECORDS[:safe_limit]
    )


def status() -> dict[str, object]:
    ids = tuple(memory_id for memory_id, _ in _RECORDS)
    return {
        "component": "Latest Founder Memory Locks",
        "ready": bool(ids) and len(ids) == len(set(ids)),
        "revision": REVISION,
        "record_count": len(ids),
        "latest_founder_correction_wins": True,
        "raw_chat_dump": False,
        "private_chain_of_thought_included": False,
        "credentials_or_secrets_included": False,
        "human_authority_final": True,
    }
