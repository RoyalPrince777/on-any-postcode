"""Curated, non-sensitive historical OAP decision memory.

History is not canonical truth. It explains how OAP arrived at the current
Founder-approved state. Superseded wording remains searchable as history but must
never override canonical memory. This module intentionally excludes credentials,
private chain-of-thought and unrelated personal data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from oap.contracts import MemoryItem, OutputState

HISTORY_REVISION = "2026-09-04-v1"
_HISTORY_TIMESTAMP = datetime(2026, 9, 4, tzinfo=timezone.utc)

_HISTORY: tuple[dict[str, object], ...] = (
    {
        "event_id": "history.naming.metadata-oapcore",
        "order": 10,
        "scopes": ("TECHNICAL", "GENERAL"),
        "summary": "SMI data/core naming evolved from metadata to oapdata to OAP CORE. OAP CORE is current canonical naming; older names remain historical/compatibility context only.",
        "superseded_by": "canonical deployment.local-first / OAP CORE naming",
    },
    {
        "event_id": "history.feed-pulse",
        "order": 20,
        "scopes": ("COMMUNITY", "GENERAL"),
        "summary": "The generic product label Feed was replaced by Pulse. Pulse is the canonical OAP feed language.",
        "superseded_by": "canonical oap.product-language",
    },
    {
        "event_id": "history.news-signal",
        "order": 30,
        "scopes": ("COMMUNITY", "GENERAL"),
        "summary": "The generic News label was replaced by Signal. Signal is the canonical OAP news language.",
        "superseded_by": "canonical oap.product-language",
    },
    {
        "event_id": "history.events-activity-adventure",
        "order": 40,
        "scopes": ("COMMUNITY", "STRATEGY", "GENERAL"),
        "summary": "Events/Gatherings wording was progressively replaced by Activity and Adventure, with Community Power Days retained for community-led event energy where appropriate.",
        "superseded_by": "canonical oap.product-language",
    },
    {
        "event_id": "history.verified-certified",
        "order": 50,
        "scopes": ("COMMUNITY", "STRATEGY", "GENERAL"),
        "summary": "Verified/Verification terminology was replaced by Certified/Certification for OAP identity and trust language.",
        "superseded_by": "canonical oap.identity-language",
    },
    {
        "event_id": "history.auth-language",
        "order": 60,
        "scopes": ("COMMUNITY", "GENERAL"),
        "summary": "Generic Create Account/Login/Logout wording was replaced by Join OAP / Enter My World / Leave My World.",
        "superseded_by": "canonical oap.identity-language",
    },
    {
        "event_id": "history.worldcup-location-model",
        "order": 70,
        "scopes": ("COMMUNITY", "TECHNICAL", "GENERAL"),
        "summary": "Early football/World Cup hierarchy placeholders were rejected as the permanent world model and replaced by the OAP geographic hierarchy from Postcode through Borough, Region, Country, Continent, Global and Beyond.",
        "superseded_by": "canonical oap.location-hierarchy",
    },
    {
        "event_id": "history.maps-third-party",
        "order": 80,
        "scopes": ("TECHNICAL", "STRATEGY", "GENERAL"),
        "summary": "Google Maps/Waze-style capabilities were retained only as inspiration/reference. OAP direction moved toward first-party/self-hosted map, routing, spatial ontology and world-state intelligence rather than third-party production control.",
        "superseded_by": "canonical maps.self-hosting",
    },
    {
        "event_id": "history.maps-dimensional-views",
        "order": 90,
        "scopes": ("TECHNICAL", "COMMUNITY", "GENERAL"),
        "summary": "OAP Maps expanded from conventional map views into selectable 2D Street, 3D World, 4D Time and 5D Intelligence views, with AUTO adaptation and a separate Cockpit experience.",
        "superseded_by": "canonical maps.dimension-modes",
    },
    {
        "event_id": "history.matrix-placement",
        "order": 100,
        "scopes": ("TECHNICAL", "GENERAL"),
        "summary": "Matrix, Nexus and Oasis were clarified as systems rather than agents. Matrix Intelligence agents were placed inside Matrix System; Nexus remained connective infrastructure and Oasis remained the human experience/presentation environment.",
        "superseded_by": "canonical smi.single-brain / matrix.role",
    },
    {
        "event_id": "history.council-intelligence-language",
        "order": 110,
        "scopes": ("STRATEGY", "GENERAL"),
        "summary": "Council terminology for institutional/animal/Akan layers was rejected in favour of Intelligence terminology.",
        "superseded_by": "current OAP Intelligence naming",
    },
    {
        "event_id": "history.piga-rejected",
        "order": 120,
        "scopes": ("STRATEGY", "GENERAL"),
        "summary": "PIGA was rejected as the governance/institutional architecture name and should not be revived as canonical naming.",
        "superseded_by": "current Intelligence-based governance naming",
    },
    {
        "event_id": "history.nirmata-created",
        "order": 130,
        "scopes": ("TECHNICAL", "STRATEGY", "GENERAL"),
        "summary": "Nirmata was introduced as NIRMATA-001, Creation Architect within Civilisation Intelligence, to convert approved visions into implementation-grade blueprints without execution or authority escalation.",
        "superseded_by": "canonical agents.registry-law",
    },
    {
        "event_id": "history.smi-seven-worlds",
        "order": 140,
        "scopes": ("TECHNICAL", "GENERAL"),
        "summary": "SMI architecture was consolidated into one brain with exactly seven Intelligence Worlds; Matrix is one world while Nexus is connective/nervous infrastructure rather than an Intelligence World.",
        "superseded_by": "canonical smi.single-brain",
    },
    {
        "event_id": "history.smi-3-7-21",
        "order": 150,
        "scopes": ("TECHNICAL", "GENERAL"),
        "summary": "SMI reasoning depth was formalised as adaptive 3/7/21 modes: Instant 3, Medium 7 and High 21, with smallest-sufficient-depth selection and escalation on uncertainty/complexity.",
        "superseded_by": "canonical smi.depth-modes",
    },
    {
        "event_id": "history.thinking-telemetry",
        "order": 160,
        "scopes": ("TECHNICAL", "GENERAL"),
        "summary": "The Sovereignty Dashboard requirement was clarified: show safe thinking-process telemetry, progress and elapsed time, but never private chain-of-thought, hidden prompts or internal reasoning tokens.",
        "superseded_by": "canonical smi.sovereignty-dashboard",
    },
    {
        "event_id": "history.sika-bank-separation",
        "order": 170,
        "scopes": ("STRATEGY", "GENERAL"),
        "summary": "SIKA was separated from banking institutions: SIKA is the currency/value system; United States of Africa Royalty Bank is the Africa-facing institution concept; a UK banking institution must use a separate UK name/legal entity.",
        "superseded_by": "canonical sika.bank-separation",
    },
    {
        "event_id": "history.telecom-foundations",
        "order": 180,
        "scopes": ("TECHNICAL", "STRATEGY", "GENERAL"),
        "summary": "Open5GS, OAI, Osmocom and OCUDU/srsRAN lineage were positioned as licence-reviewed upstream foundations beneath OAP-owned telecom control rather than permanent OAP product identities.",
        "superseded_by": "canonical connectivity.opensource",
    },
    {
        "event_id": "history.6g7g-clarification",
        "order": 190,
        "scopes": ("TECHNICAL", "STRATEGY", "GENERAL"),
        "summary": "Connectivity was clarified as operational architecture for legacy/4G/5G plus a separate 6G/7G research branch. 6G can graduate into operations when mature; 7G remains longer-horizon post-6G research.",
        "superseded_by": "canonical connectivity.operational / connectivity.6g7g",
    },
    {
        "event_id": "history.rf-guardian",
        "order": 200,
        "scopes": ("TECHNICAL", "MONITORING", "GENERAL"),
        "summary": "RF/Wi-Fi/ISAC sensing was admitted only as a governed Matrix sensor class with local-first processing, privacy reduction and explicit Guardian boundaries against covert personal surveillance.",
        "superseded_by": "canonical matrix.rf-guardian",
    },
    {
        "event_id": "history.founder-only-private",
        "order": 210,
        "scopes": ("TECHNICAL", "STRATEGY", "GENERAL"),
        "summary": "Private Mission/Founder access was hardened to fail closed: public browsing remains anonymous where intended, while profile creation/private dashboard access remains Founder-only under the current rule.",
        "superseded_by": "canonical oap.public-private",
    },
    {
        "event_id": "history.autonomy-a3",
        "order": 220,
        "scopes": ("TECHNICAL", "MONITORING", "GENERAL"),
        "summary": "SMI autonomy progressed from observe/reason/propose to bounded A3 for pre-authorised reversible runtime heartbeat/health actions only, while consequential execution, self-approval, deploy, spend, migrations and permission changes remain blocked.",
        "superseded_by": "canonical smi.autonomy-boundary",
    },
)


def historical_memory_items(
    task_type: str | None = None,
    *,
    limit: int = 6,
) -> tuple[MemoryItem, ...]:
    """Return bounded historical context; canonical truth always outranks it."""

    task = str(task_type or "GENERAL").strip().upper() or "GENERAL"
    safe_limit = min(max(int(limit), 1), 12)
    exact = [record for record in _HISTORY if task in record["scopes"]]
    general = [
        record
        for record in _HISTORY
        if "GENERAL" in record["scopes"] and record not in exact
    ]
    selected = sorted(exact + general, key=lambda item: int(item["order"]), reverse=True)
    return tuple(
        MemoryItem(
            memory_id=f"history:{record['event_id']}",
            task_type="HISTORICAL",
            summary=(
                f"HISTORY ONLY — {record['summary']} "
                f"Superseded/current authority: {record['superseded_by']}."
            ),
            output_state=OutputState.SYSTEM_LOG_ONLY.value,
            created_at=_HISTORY_TIMESTAMP,
        )
        for record in selected[:safe_limit]
    )


def status() -> dict[str, object]:
    ids = tuple(str(record["event_id"]) for record in _HISTORY)
    return {
        "component": "OAP Historical Memory",
        "ready": bool(ids) and len(ids) == len(set(ids)),
        "revision": HISTORY_REVISION,
        "record_count": len(ids),
        "canonical_authority": False,
        "latest_founder_correction_wins": True,
        "sensitive_personal_backfill_included": False,
        "private_reasoning_included": False,
        "human_authority_final": True,
    }
