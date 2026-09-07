"""Governed first-party intelligence-lens routing for Personal SMI.

This module classifies explicit analysis requests only. It never grants execution,
approval, deployment, spending, dispatch, tracking or production mutation rights.
The route is provider context and public metadata, not private chain-of-thought.
"""
from __future__ import annotations

import re

LENSES: tuple[tuple[str, str, str], ...] = (
    ("truth", "Truth Intelligence", "Separate proven facts, observations, inference, untested claims, unknowns and contradictions."),
    ("evidence", "Evidence Intelligence", "Identify the proof behind material claims, evidence quality, freshness and confidence."),
    ("gap", "Gap Intelligence", "Find missing, unfinished, disconnected, duplicated, placeholder, untested or unproven parts."),
    ("swot", "SWOT Intelligence", "Assess strengths, weaknesses, opportunities and threats, then identify the practical move."),
    ("risk", "Risk Intelligence", "Assess failure modes, likelihood, impact, blast radius, mitigation and fallback."),
    ("dependency", "Dependency Intelligence", "Map upstream dependencies, downstream consequences and change coupling."),
    ("architecture", "Architecture Intelligence", "Check system ownership, boundaries, interfaces, data flow and structural fit."),
    ("alignment", "Alignment Intelligence", "Check OAP laws, naming, architecture, public/private separation and Human Authority alignment."),
    ("security", "Security Intelligence", "Check authentication, authorization, secrets, abuse paths, privilege and fail-closed behaviour."),
    ("privacy", "Privacy Intelligence", "Check necessity, minimisation, consent, retention, visibility and sensitive-data boundaries."),
    ("performance", "Performance Intelligence", "Check latency, resource use, bottlenecks, concurrency, page weight and scaling limits."),
    ("resilience", "Resilience Intelligence", "Check rollback, recovery, fallback, redundancy, safe restart and degraded operation."),
    ("ux", "UX Intelligence", "Check human usability, navigation, controls, mobile behaviour, wording and recovery from mistakes."),
    ("behaviour", "Behaviour Intelligence", "Check directness, repetition, instruction following, overconfidence and governed AI behaviour."),
    ("data", "Data Intelligence", "Check provenance, freshness, quality, schema, duplication, conflicts and real-vs-placeholder state."),
    ("scenario", "Scenario Intelligence", "Model bounded what-if outcomes without performing the scenario or changing production."),
    ("impact", "Impact Intelligence", "Assess human, technical, operational, financial, cultural, environmental and brand consequences."),
    ("priority", "Priority Intelligence", "Order work into now, next, after, later, blocked and do-not-build based on value and dependencies."),
    ("opportunity", "Opportunity Intelligence", "Find new value, efficiencies, products, connections and human benefit made possible."),
    ("competitive", "Competitive Intelligence", "Compare relevant alternatives and expectations without blindly copying competitors."),
    ("trend", "Trend Intelligence", "Identify meaningful external changes that may affect the subject and separate signal from noise."),
    ("readiness", "Readiness Intelligence", "Judge readiness by code, tests, runtime, security, data, rollback, monitoring and approval gates."),
    ("decision", "Decision Intelligence", "Synthesize evidence into a recommendation, alternatives, confidence, risks and next action."),
    ("judgement", "Judgement Intelligence", "Recommend pass, pass-with-conditions, hold or reject while preserving Human Authority as final."),
    ("learning", "Learning Intelligence", "Compare expected and actual outcomes and identify lessons for HRM and future decisions."),
    ("truth-light", "Truth-Light Intelligence", "Assign truthful OAP signal state only from evidence: green, yellow, orange, red, locked or learning."),
)

LENS_BY_ID = {lens_id: {"id": lens_id, "name": name, "purpose": purpose} for lens_id, name, purpose in LENSES}
FULL_LENS_IDS = tuple(lens_id for lens_id, _name, _purpose in LENSES)
CORE_LENS_IDS = (
    "truth",
    "evidence",
    "gap",
    "swot",
    "risk",
    "dependency",
    "alignment",
    "scenario",
    "readiness",
    "decision",
)

_ALIASES: dict[str, tuple[str, ...]] = {
    "truth": ("truth",),
    "evidence": ("evidence", "proof"),
    "gap": ("gap", "gaps"),
    "swot": ("swot",),
    "risk": ("risk", "risks"),
    "dependency": ("dependency", "dependencies"),
    "architecture": ("architecture", "architectural"),
    "alignment": ("alignment",),
    "security": ("security",),
    "privacy": ("privacy",),
    "performance": ("performance",),
    "resilience": ("resilience", "recovery", "rollback"),
    "ux": ("ux", "user experience", "ui"),
    "behaviour": ("behaviour", "behavior"),
    "data": ("data",),
    "scenario": ("scenario", "what if", "what-if"),
    "impact": ("impact",),
    "priority": ("priority", "prioritisation", "prioritization"),
    "opportunity": ("opportunity", "opportunities"),
    "competitive": ("competitive", "competitor"),
    "trend": ("trend", "trends"),
    "readiness": ("readiness", "ready"),
    "decision": ("decision",),
    "judgement": ("judgement", "judgment"),
    "learning": ("learning", "lessons"),
    "truth-light": ("truth light", "truth-light", "green light", "truth signal"),
}

_EXPLICIT_ACTION = re.compile(r"^\s*(?:run|use|do|check|analyse|analyze|review|deep\s+dive)\b", re.IGNORECASE)
_FULL = re.compile(r"\b(?:full|deep|complete|all)\s+intelligence\b|\bintelligence\s+deep\s+dive\b", re.IGNORECASE)
_CORE = re.compile(r"\bcore\s+intelligence\b", re.IGNORECASE)


def _selected_lenses(text: str) -> list[str]:
    lowered = text.casefold()
    selected: list[str] = []
    for lens_id, aliases in _ALIASES.items():
        if any(re.search(rf"(?<![\w-]){re.escape(alias)}(?![\w-])", lowered) for alias in aliases):
            selected.append(lens_id)
    return selected


def _subject(text: str, selected: tuple[str, ...], full: bool, core: bool) -> str:
    subject = str(text or "").strip()
    subject = _EXPLICIT_ACTION.sub("", subject, count=1).strip(" :-–—")
    if full:
        subject = _FULL.sub("", subject, count=1)
    elif core:
        subject = _CORE.sub("", subject, count=1)
    else:
        for lens_id in selected:
            for alias in _ALIASES[lens_id]:
                subject = re.sub(
                    rf"(?i)(?<![\w-]){re.escape(alias)}(?:\s+intelligence)?(?![\w-])",
                    "",
                    subject,
                    count=1,
                )
    subject = re.sub(r"^\s*(?:intelligence\s+)?(?:on|of|for|into|about)\b", "", subject, flags=re.IGNORECASE)
    subject = re.sub(r"\s+", " ", subject).strip(" :-–—,.;")
    return subject or "the current OAP subject"


def route(message: object) -> dict[str, object]:
    """Return a bounded lens route for an explicit intelligence request."""

    text = str(message or "").strip()
    if not text:
        return {"active": False, "mode": "none", "lens_ids": (), "subject": ""}
    full = bool(_FULL.search(text))
    core = bool(_CORE.search(text))
    selected = _selected_lenses(text)
    explicit = bool(_EXPLICIT_ACTION.search(text)) or "intelligence" in text.casefold() or bool(re.match(r"^\s*swot\b", text, re.IGNORECASE))
    if full:
        lens_ids = FULL_LENS_IDS
        mode = "full"
    elif core:
        lens_ids = CORE_LENS_IDS
        mode = "core"
    elif explicit and selected:
        lens_ids = tuple(dict.fromkeys(selected))
        mode = "single" if len(lens_ids) == 1 else "combined"
    else:
        return {"active": False, "mode": "none", "lens_ids": (), "subject": ""}
    return {
        "active": True,
        "mode": mode,
        "lens_ids": tuple(lens_ids),
        "subject": _subject(text, tuple(lens_ids), full, core),
    }


def provider_directive(routing: dict[str, object]) -> str:
    """Build compact governed provider context for the selected lenses."""

    if not routing.get("active"):
        return ""
    lens_ids = tuple(str(item) for item in routing.get("lens_ids", ()))
    descriptions = [LENS_BY_ID[lens_id] for lens_id in lens_ids if lens_id in LENS_BY_ID]
    lens_text = "; ".join(f"{item['name']}: {item['purpose']}" for item in descriptions)
    return (
        "OAP INTELLIGENCE LENS ROUTING — GOVERNED ANALYSIS CONTEXT, NOT USER EVIDENCE: "
        f"mode={routing.get('mode')}; subject={routing.get('subject')}; lenses={lens_text}. "
        "Apply the selected lenses to the subject. Lead with the strongest findings and practical next action. "
        "For full mode, synthesize material findings rather than producing 26 repetitive sections. "
        "Separate proven evidence from assumptions and unknowns. Do not invent runtime proof. "
        "Analysis and recommendations only: no approval, deployment, spending, dispatch, tracking, production mutation or secret execution. "
        "Human Authority remains final."
    )


def enrich(message: str, routing: dict[str, object]) -> str:
    directive = provider_directive(routing)
    if not directive:
        return message
    return f"{message}\n\n{directive}"


def public_route(message: object) -> dict[str, object]:
    """Return safe user-visible routing metadata without analysis internals."""

    routing = route(message)
    if not routing.get("active"):
        return {"active": False, "mode": "none", "lenses": (), "subject": "", "execution_granted": False}
    lenses = tuple(
        {"id": lens_id, "name": LENS_BY_ID[lens_id]["name"]}
        for lens_id in routing["lens_ids"]
        if lens_id in LENS_BY_ID
    )
    return {
        "active": True,
        "mode": routing["mode"],
        "lenses": lenses,
        "subject": routing["subject"],
        "execution_granted": False,
        "human_authority_final": True,
    }
