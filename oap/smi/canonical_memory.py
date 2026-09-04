"""Founder-approved canonical OAP memory available to the SMI Brain.

This module is a curated project-memory manifest, not a dump of private model
state. It intentionally excludes credentials, secrets, private chain-of-thought,
hidden prompts and unrelated personal data. Latest explicit Founder corrections
win over older historical wording.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from oap.contracts import MemoryItem, OutputState

CANONICAL_MEMORY_REVISION = "2026-09-04"
CANONICAL_MEMORY_PROVENANCE = "founder-approved-oap-memory-sync"
_CANONICAL_TIMESTAMP = datetime(2026, 9, 4, tzinfo=timezone.utc)

# Each record is deliberately concise so SMI can load the smallest relevant
# context rather than flooding every request with the full project history.
_CANONICAL_RECORDS: tuple[dict[str, Any], ...] = (
    {
        "memory_id": "oap.front-door",
        "scopes": ("GENERAL", "COMMUNITY", "STRATEGY", "TECHNICAL"),
        "summary": "OAP public architecture principle: One World -> One Front Door -> Many Systems Inside. OAP World is the public front door; high-risk or regulated systems remain separated for clarity, performance, security and compliance.",
    },
    {
        "memory_id": "oap.brand-core",
        "scopes": ("GENERAL", "COMMUNITY", "CULTURE", "STRATEGY"),
        "summary": "ON ANY POSTCODE tagline: Born Local. Built Global. Earth is our turf. Human-first framing includes One race: Human race. OAP English is primary product language; Twi may be optional later.",
    },
    {
        "memory_id": "oap.public-private",
        "scopes": ("GENERAL", "TECHNICAL", "STRATEGY"),
        "summary": "Public and private surfaces are separate. Anonymous public browsing is allowed. Founder/private dashboard access fails closed; only Human Authority may create the Founder profile or access the private dashboard under the current Founder-only rule.",
    },
    {
        "memory_id": "oap.identity-language",
        "scopes": ("GENERAL", "COMMUNITY", "STRATEGY"),
        "summary": "Canonical identity language: Join OAP, Enter My World, Leave My World. Use Certified/Certification instead of Verified/Verification across identity and trust language.",
    },
    {
        "memory_id": "oap.location-hierarchy",
        "scopes": ("GENERAL", "COMMUNITY", "TECHNICAL"),
        "summary": "Canonical OAP geography: Postcode/Home Point -> Borough/Local Cluster -> County or Region/Regional Layer -> Country/National Realm -> Continent/Cultural Block -> Global/World View -> Universe/Beyond Layer. Replace old football-first world hierarchy with this permanent location model.",
    },
    {
        "memory_id": "oap.product-language",
        "scopes": ("GENERAL", "COMMUNITY", "STRATEGY"),
        "summary": "Core OAP product language includes The Spot, Pulse=feed, Signal=news, The Link=opportunities, Link Up=chat inside The Link, My World, OAP TV, OAP Market and Explorer. Profile is the stage to My Card. Youth Club is preferred over Youth. Activity/Adventure are preferred over generic Events/Gatherings where applicable.",
    },
    {
        "memory_id": "oap.link-language",
        "scopes": ("GENERAL", "COMMUNITY"),
        "summary": "Canonical The Link real-time vocabulary: Chat -> Link Up; message -> Link; group chat -> Circle; voice note -> Voice; audio call -> Call; video call -> Face Up; presence -> Around Now; status -> Now; available -> I'm Free; delivered -> Landed; read -> Seen; invite -> Bring In; join -> Link In; leave -> Step Out; location share -> Share My Spot; live location -> Live Spot.",
    },
    {
        "memory_id": "oap.no-ads-local-first",
        "scopes": ("GENERAL", "STRATEGY", "TECHNICAL"),
        "summary": "OAP direction is no ads and local-first/first-party control. Heavy engines should be separated behind lightweight user-facing surfaces. External/open components may bootstrap selected layers, but OAP owns control, data, configuration, orchestration, observability and long-term evolution.",
    },
    {
        "memory_id": "smi.single-brain",
        "scopes": ("GENERAL", "TECHNICAL", "STRATEGY"),
        "summary": "SMI means Sovereign Megaverse Intelligence and is one brain. It has exactly seven Intelligence Worlds; Matrix is one of them. Nexus is the connective/nervous system, not an Intelligence World. Oasis is the environment/presentation layer. OAP Core provides connective context. The Thalamus routes internally. Systems are not agents.",
    },
    {
        "memory_id": "smi.brain-anatomy",
        "scopes": ("GENERAL", "TECHNICAL"),
        "summary": "SMI Brain organisation is grounded in real brain anatomy: hemispheres, frontal/parietal/temporal/occipital lobes, corpus callosum, thalamus, hypothalamus, hippocampus, amygdala, cerebellum and brainstem are the organising model rather than generic software-module naming.",
    },
    {
        "memory_id": "smi.governance-path",
        "scopes": ("GENERAL", "TECHNICAL", "STRATEGY"),
        "summary": "Canonical organism governance path: OAP Core -> Nexus -> Thalamus -> SMI Brain -> Judgement -> Human Authority -> Living Kernel -> Body Organ -> HRM. Human Authority remains final for consequential decisions.",
    },
    {
        "memory_id": "smi.hrm-laws",
        "scopes": ("GENERAL", "TECHNICAL", "STRATEGY"),
        "summary": "HRM governance uses 3 layers x 7 active laws = 21 steps. Core laws include proof before execution, verification before sharing, compliance before public claims, community before middlemen, ownership before dependency, audit before automation and human approval before real-world action.",
    },
    {
        "memory_id": "smi.depth-modes",
        "scopes": ("GENERAL", "TECHNICAL"),
        "summary": "SMI adaptive depth modes are Instant=3, Medium=7 and High=21 (3x7). SMI should choose the smallest sufficient depth, escalate on uncertainty/complexity and finish early when enough evidence exists. Instant may bypass unnecessary deeper deliberation but never Guardian, identity, permission, provenance, safety or Human Authority gates.",
    },
    {
        "memory_id": "smi.sovereignty-dashboard",
        "scopes": ("GENERAL", "TECHNICAL"),
        "summary": "SMI Sovereignty Dashboard may expose observable telemetry such as selected mode, depth, stage/progress, elapsed time, confidence, sources/tools/agents used and Guardian status. It must never expose private chain-of-thought, hidden system prompts, private reasoning tokens, credentials or internal secrets. Human-readable answer rationale is allowed.",
    },
    {
        "memory_id": "smi.autonomy-boundary",
        "scopes": ("GENERAL", "TECHNICAL", "MONITORING"),
        "summary": "SMI autonomy is bounded and audited. It may observe, self-check, re-check coherence, retry safe non-consequential analysis, queue safe intents and propose improvements. It may not self-approve, change permissions/constitution, self-promote, deploy unreviewed code, spend/transfer value, perform production migrations, dispatch consequential real-world actions or bypass Human Authority.",
    },
    {
        "memory_id": "agents.registry-law",
        "scopes": ("GENERAL", "TECHNICAL"),
        "summary": "Agents are registered specialists, one family per agent, duplicate-checked and fully audited. External providers remain external rather than being misrepresented as OAP agents. Nirmata (NIRMATA-001) is the Creation Architect: transforms approved human ideas into blueprints/specifications but cannot deploy, override Human Authority, change its permissions/constitution or create unregistered agents.",
    },
    {
        "memory_id": "matrix.role",
        "scopes": ("GENERAL", "TECHNICAL", "COMMUNITY"),
        "summary": "Matrix is OAP spatial/world-state intelligence: what exists, where it is, what is happening, what changed and how things are connected. Matrix Intelligence agents belong inside the Matrix system rather than being loose general agents.",
    },
    {
        "memory_id": "maps.dimension-modes",
        "scopes": ("GENERAL", "TECHNICAL", "COMMUNITY"),
        "summary": "OAP Maps selectable views: 2D=Street, 3D=World, 4D=Time (3D space plus history/live change/forecast), 5D=Intelligence (4D plus context, relationships and meaning; not a literal fifth physical dimension). AUTO may adapt presentation while users retain manual control. Vehicle/Cockpit presentation is separate from dimensional view.",
    },
    {
        "memory_id": "maps.stack",
        "scopes": ("GENERAL", "TECHNICAL"),
        "summary": "OAP Maps stack: OAP Maps is the human interface; OAP Spatial Core is the first-party map engine; Matrix models world state; Nexus connects systems; Oasis presents useful human experience; HRM supplies temporal memory; Guardian protects boundaries; SMI reasons over the result. Use best ideas from major map/navigation systems without copying their product identity or making them the OAP brain.",
    },
    {
        "memory_id": "maps.journey-intelligence",
        "scopes": ("GENERAL", "TECHNICAL", "COMMUNITY"),
        "summary": "OAP Journey should be context-aware rather than fastest-route-only: walking, cycling, driving, vans, public transport, EV, delivery and accessibility can consider traffic, hazards, weather, time, energy/range, cost, accessibility and user preference. Community road signals feed Matrix with provenance, time, confidence and privacy classification.",
    },
    {
        "memory_id": "matrix.rf-guardian",
        "scopes": ("GENERAL", "TECHNICAL", "MONITORING"),
        "summary": "Matrix RF Intelligence is a governed specialist capability inside Matrix. Raw RF should stay local/edge where practical; Matrix receives privacy-reduced abstractions. No covert human identification, through-wall personal surveillance, biometric inference by default or neighbouring-property sensing without an appropriate basis. Sensing is user-controllable and retention-limited through Guardian RF.",
    },
    {
        "memory_id": "connectivity.operational",
        "scopes": ("GENERAL", "TECHNICAL", "MONITORING"),
        "summary": "OAP Connectivity is an operational sovereign architecture, not only research: OAP Network Core, OAP Radio Access, OAP Edge, Guardian RF, Matrix RF Intelligence, observability, subscriber/identity/policy/orchestration, legacy 2G/3G paths and 4G/5G deployment paths where legally permitted.",
    },
    {
        "memory_id": "connectivity.opensource",
        "scopes": ("TECHNICAL", "STRATEGY"),
        "summary": "Open-source telecom stacks such as Osmocom, Open5GS, OAI and OCUDU/srsRAN lineage are audited, licence-reviewed upstream foundations beneath OAP-owned control, deployment, data, configuration, orchestration and evolution; they are not permanent OAP product identities. Upstream copyright/licence obligations remain respected.",
    },
    {
        "memory_id": "connectivity.6g7g",
        "scopes": ("GENERAL", "TECHNICAL", "STRATEGY"),
        "summary": "OAP 6G/7G Lab is the forward research branch. 6G covers AIAC, ISAC, AI-assisted/AI-native PHY research, NTN and edge integration and may graduate into operations as standards/evidence mature. 7G is longer-horizon post-6G research including advanced NTN/satellite, mesh/device-to-device, future spectrum/compute/network concepts. Radio survival > AI workload; deterministic radio fallback remains mandatory.",
    },
    {
        "memory_id": "sika.bank-separation",
        "scopes": ("GENERAL", "STRATEGY"),
        "summary": "SIKA is the currency/value system, not a bank. United States of Africa Royalty Bank is the future Africa-facing regulated banking institution concept. The UK banking institution must have a separate UK name and legal entity. SIKA may later be usable across more than one properly regulated institution.",
    },
    {
        "memory_id": "sika.launch-boundary",
        "scopes": ("GENERAL", "STRATEGY"),
        "summary": "At launch SIKA is framed as loyalty/contribution points, internal credits, vouchers or collectibles rather than legal tender. Banking/e-money claims and regulated financial functions require the appropriate legal/regulatory route and remain separated from OAP World.",
    },
    {
        "memory_id": "deployment.local-first",
        "scopes": ("TECHNICAL", "MONITORING"),
        "summary": "OAP stack direction includes Flask/SQLite/Termux locally, Ollama local AI and Render/GitHub remotely, with separate public/private services. Production actions must be evidenced, fail closed where required and preserve Human Authority. Public routing/provider experiments remain verification-only until capacity, monitoring and runtime gates pass.",
    },
    {
        "memory_id": "maps.self-hosting",
        "scopes": ("TECHNICAL", "STRATEGY"),
        "summary": "Long-term OAP maps/navigation direction is self-hosted and first-party controlled: open geographic data and routing foundations may be used under their licences, while OAP owns its spatial ontology, routing intelligence, world-state model, UI, memory, orchestration and privacy boundaries rather than depending on Google Maps/Waze as the production brain.",
    },
    {
        "memory_id": "memory.latest-wins",
        "scopes": ("GENERAL", "TECHNICAL", "STRATEGY"),
        "summary": "Canonical SMI memory rule: latest explicit Founder correction wins. Reconcile older memories rather than blindly accumulating contradictions. Hidden prompts, private chain-of-thought, credentials/secrets and unrelated personal data are never part of canonical SMI memory.",
    },
)


def _record_digest_payload() -> bytes:
    payload = [
        {
            "memory_id": record["memory_id"],
            "scopes": list(record["scopes"]),
            "summary": record["summary"],
        }
        for record in _CANONICAL_RECORDS
    ]
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


CANONICAL_MEMORY_DIGEST = hashlib.sha256(_record_digest_payload()).hexdigest()


def canonical_memory_items(
    task_type: str | None = None,
    *,
    limit: int = 21,
) -> tuple[MemoryItem, ...]:
    """Return bounded canonical project memory relevant to one task family."""

    task = str(task_type or "GENERAL").strip().upper() or "GENERAL"
    safe_limit = min(max(int(limit), 1), 21)
    exact = [record for record in _CANONICAL_RECORDS if task in record["scopes"]]
    general = [
        record
        for record in _CANONICAL_RECORDS
        if "GENERAL" in record["scopes"] and record not in exact
    ]
    selected = (exact + general)[:safe_limit]
    return tuple(
        MemoryItem(
            memory_id=f"canonical:{record['memory_id']}",
            task_type="CANONICAL",
            summary=str(record["summary"]),
            output_state=OutputState.SYSTEM_LOG_ONLY.value,
            created_at=_CANONICAL_TIMESTAMP,
        )
        for record in selected
    )


def status() -> dict[str, object]:
    """Expose provenance and integrity telemetry without exposing private memory."""

    ids = tuple(str(record["memory_id"]) for record in _CANONICAL_RECORDS)
    return {
        "component": "Canonical SMI Memory",
        "ready": len(ids) == len(set(ids)) and bool(ids),
        "revision": CANONICAL_MEMORY_REVISION,
        "provenance": CANONICAL_MEMORY_PROVENANCE,
        "record_count": len(ids),
        "digest": CANONICAL_MEMORY_DIGEST,
        "latest_founder_correction_wins": True,
        "private_chain_of_thought_included": False,
        "hidden_prompts_included": False,
        "credentials_or_secrets_included": False,
        "unrelated_personal_data_included": False,
        "human_authority_final": True,
    }
