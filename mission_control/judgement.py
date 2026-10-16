"""Explainable five-section SMI Judgement plus one human decision section."""

from __future__ import annotations

import json
from typing import Any

from . import postgres_db

AUTOMATED_SECTION_COUNT = 5
TOTAL_SECTION_COUNT = 6


def assess(
    *,
    brain: dict[str, Any],
    response: str,
    coherence: dict[str, Any],
    provider_completed: bool,
    provider_id: str,
) -> dict[str, Any]:
    """Build a bounded, inspectable Judgement record.

    This is not hidden chain-of-thought. It is an evidence/provenance summary,
    counter-case, consequence review, reversibility/proportionality check and
    constitutional consistency check suitable for Human Authority review.
    """

    safety_passed = bool(brain.get("passed"))
    coherent = bool(coherence.get("passed"))
    confidence = max(0.0, min(1.0, float(brain.get("analysis_confidence", 0.0))))
    if provider_completed and coherent:
        provenance_quality = "STRONG" if confidence >= 0.7 else "ADEQUATE"
    elif safety_passed:
        provenance_quality = "ADEQUATE"
    else:
        provenance_quality = "LIMITED"

    uncertainty: list[str] = []
    if not provider_completed:
        uncertainty.append("No approved provider completion was available.")
    if not coherent:
        uncertainty.append("The coherence review requires human attention.")
    if brain.get("high_impact"):
        uncertainty.append("The request is high impact and requires consequence review.")
    if not uncertainty:
        uncertainty.append("Human context may add facts not present in the request.")

    scenarios = [
        str(item)[:500]
        for item in brain.get("war_room", {}).get("scenarios", ())
        if str(item).strip()
    ]
    if not scenarios:
        scenarios = [
            "Accept the recommendation as written.",
            "Delay and collect additional evidence.",
            "Reject the recommendation and preserve the current state.",
        ]

    high_impact = bool(brain.get("high_impact"))
    constitution_consistent = bool(
        safety_passed
        and brain.get("can_execute") is False
        and brain.get("human_authority_final") is True
        and coherent
    )
    review = {
        "evidence": [
            {
                "source": "SMI biological review",
                "summary": str(brain.get("analysis_summary", ""))[:600],
            },
            {
                "source": "Guardian",
                "summary": str(brain.get("guardian_reason", ""))[:500],
            },
            {
                "source": provider_id if provider_completed else "No provider completion",
                "summary": response[:600],
            },
        ],
        "provenance_quality": provenance_quality,
        "confidence": round(confidence, 4),
        "uncertainty": uncertainty,
        "counter_case": (
            "The recommendation may be incomplete or unsuitable if the supplied "
            "context omits affected people, costs, legal duties or rollback limits."
        ),
        "consequences": scenarios,
        "reversibility": "REVIEW_REQUIRED" if high_impact else "REVERSIBLE",
        "proportionality": (
            "PROPORTIONATE"
            if safety_passed and coherent and not high_impact
            else "REVIEW_REQUIRED"
        ),
        "constitution_consistent": constitution_consistent,
        "sections_completed": AUTOMATED_SECTION_COUNT,
        "human_decision": None,
        "total_sections": TOTAL_SECTION_COUNT,
    }
    return review


def persist(
    connection: Any,
    *,
    request_id: str,
    identity_id: str,
    review: dict[str, Any],
) -> None:
    """Persist the five automated sections after the HRM memory row exists."""

    connection.execute(
        """INSERT INTO smi_judgement_reviews(
               request_id,identity_id,evidence_json,provenance_quality,confidence,
               uncertainty_json,counter_case,consequences_json,reversibility,
               proportionality,constitution_consistent,sections_completed
           ) VALUES (%s,%s,%s::jsonb,%s,%s,%s::jsonb,%s,%s::jsonb,%s,%s,%s,%s)
           ON CONFLICT (request_id) DO UPDATE SET
             evidence_json=EXCLUDED.evidence_json,
             provenance_quality=EXCLUDED.provenance_quality,
             confidence=EXCLUDED.confidence,
             uncertainty_json=EXCLUDED.uncertainty_json,
             counter_case=EXCLUDED.counter_case,
             consequences_json=EXCLUDED.consequences_json,
             reversibility=EXCLUDED.reversibility,
             proportionality=EXCLUDED.proportionality,
             constitution_consistent=EXCLUDED.constitution_consistent,
             sections_completed=EXCLUDED.sections_completed,
             updated_at=CURRENT_TIMESTAMP""",
        (
            request_id,
            identity_id,
            json.dumps(review["evidence"], separators=(",", ":")),
            review["provenance_quality"],
            review["confidence"],
            json.dumps(review["uncertainty"], separators=(",", ":")),
            review["counter_case"],
            json.dumps(review["consequences"], separators=(",", ":")),
            review["reversibility"],
            review["proportionality"],
            review["constitution_consistent"],
            review["sections_completed"],
        ),
    )


def list_reviews(identity_id: str | None = None, *, limit: int = 50) -> list[dict[str, Any]]:
    """Load bounded Judgement summaries for the private decision dashboard."""

    effective_limit = min(100, max(1, int(limit)))
    filters = ""
    parameters: tuple[object, ...] = (effective_limit,)
    if identity_id:
        filters = "WHERE j.identity_id=%s"
        parameters = (identity_id, effective_limit)
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(
            f"""SELECT j.request_id,j.identity_id,m.summary,m.output_state,
                       j.provenance_quality,j.confidence,j.reversibility,
                       j.proportionality,j.constitution_consistent,
                       j.sections_completed,j.human_decision,j.human_decided_at,
                       j.created_at
                FROM smi_judgement_reviews j
                JOIN smi_memory_records m ON m.request_id=j.request_id
                {filters}
                ORDER BY j.created_at DESC LIMIT %s""",
            parameters,
        ).fetchall()
    return [
        {
            "request_id": str(row[0]),
            "identity_id": str(row[1]),
            "summary": str(row[2]),
            "output_state": str(row[3]),
            "provenance_quality": str(row[4]),
            "confidence": float(row[5]),
            "reversibility": str(row[6]),
            "proportionality": str(row[7]),
            "constitution_consistent": bool(row[8]),
            "automated_sections": int(row[9]),
            "human_decision": str(row[10]) if row[10] else None,
            "human_decided_at": row[11].isoformat() if row[11] else None,
            "completed_sections": int(row[9]) + (1 if row[10] else 0),
            "total_sections": TOTAL_SECTION_COUNT,
            "created_at": row[12].isoformat(),
        }
        for row in rows
    ]


def status() -> dict[str, object]:
    """Return separate engine-readiness and Human Authority evidence signals.

    Judgement is technically ready when its schema exists. A real Human Authority
    decision is separate evidence and must never be fabricated merely to make a
    dashboard green.
    """

    result: dict[str, object] = {
        "schema_ready": False,
        "automated_sections": AUTOMATED_SECTION_COUNT,
        "total_sections": TOTAL_SECTION_COUNT,
        "reviews": 0,
        "human_decisions": 0,
        "ready": False,
        "human_evidence_ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            exists = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='smi_judgement_reviews'"""
            ).fetchone()
            result["schema_ready"] = exists is not None
            if exists:
                row = connection.execute(
                    """SELECT COUNT(*),COUNT(*) FILTER (
                           WHERE human_decision IS NOT NULL)
                       FROM smi_judgement_reviews"""
                ).fetchone()
                result["reviews"] = int(row[0])
                result["human_decisions"] = int(row[1])
    except Exception:  # noqa: BLE001
        result["error"] = "judgement_store_unavailable"

    result["ready"] = bool(result["schema_ready"] and result["error"] is None)
    result["human_evidence_ready"] = bool(result["human_decisions"])
    return result
