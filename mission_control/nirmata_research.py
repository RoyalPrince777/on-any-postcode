"""Bounded, evidence-first Nirmata research architecture; no execution authority.

Research lenses are analytical prompts, not clinical or scientific certifications.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256

ANATOMY_LENSES = (
    "structure", "composition", "organisation", "function", "interaction",
    "energy", "information", "communication", "regulation", "balance",
    "movement", "transformation", "protection", "repair", "adaptation",
    "development", "dependency", "resilience", "emergence", "limits", "invention",
)

def research_blueprint(*, question: str, domain: str, sources: Mapping[str, str],
                       hypotheses: list[str], lenses: list[str]) -> dict[str, object]:
    """Create a deterministic advisory research record with explicit evidence gaps.

    Sources map stable identifiers to attributable references; no source is
    independently verified by this function. No health, identity or deployment
    decision is authorised by the output.
    """
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        raise ValueError("A bounded research question is required")
    if not isinstance(domain, str) or not domain.strip() or len(domain) > 120:
        raise ValueError("A bounded domain is required")
    if not isinstance(sources, Mapping) or len(sources) > 50:
        raise ValueError("Sources must be a bounded mapping")
    if not isinstance(hypotheses, list) or len(hypotheses) > 20:
        raise ValueError("Hypotheses must be a bounded list")
    if not isinstance(lenses, list) or len(lenses) > len(ANATOMY_LENSES):
        raise ValueError("Lenses must be a bounded list")
    if any(not isinstance(k, str) or not k.strip() or len(k) > 120 or
           not isinstance(v, str) or not v.strip() or len(v) > 1000
           for k, v in sources.items()):
        raise ValueError("Every source requires a bounded identifier and reference")
    if any(not isinstance(h, str) or not h.strip() or len(h) > 1000 for h in hypotheses):
        raise ValueError("Every hypothesis must be bounded text")
    if any(not isinstance(l, str) or l not in ANATOMY_LENSES for l in lenses):
        raise ValueError("Unknown anatomy lens")
    if len(set(lenses)) != len(lenses):
        raise ValueError("Duplicate anatomy lenses")
    record = {
        "agent": "Nirmata",
        "kind": "advisory_research_blueprint",
        "question": question.strip(),
        "domain": domain.strip(),
        "sources": dict(sorted(sources.items())),
        "hypotheses": list(hypotheses),
        "lenses": list(lenses),
        "evidence_status": "unverified_references" if sources else "missing",
        "verification_required": True,
        "execution_authorised": False,
        "medical_diagnosis_authorised": False,
        "identity_issuance_authorised": False,
        "human_authority": "Founder Final; Guardian and specialist review required",
    }
    record["provenance_sha256"] = sha256(
        json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return record


def verify_blueprint_integrity(record: Mapping[str, object]) -> bool:
    """Verify an advisory record has not changed since its provenance was sealed.

    Integrity does not establish scientific validity or verify external sources.
    """
    if not isinstance(record, Mapping):
        return False
    digest = record.get("provenance_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        return False
    if record.get("kind") != "advisory_research_blueprint":
        return False
    if record.get("execution_authorised") is not False:
        return False
    if record.get("medical_diagnosis_authorised") is not False:
        return False
    if record.get("identity_issuance_authorised") is not False:
        return False
    unsigned = {key: value for key, value in record.items() if key != "provenance_sha256"}
    try:
        actual = sha256(json.dumps(unsigned, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    except (TypeError, ValueError):
        return False
    return actual == digest
