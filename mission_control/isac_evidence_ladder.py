"""Seven-level OAP/SMI ISAC evidence ladder.

Evidence class, confidence and action authority are deliberately separate.
No lower evidence class may silently promote itself to a physical-world claim.
"""
from __future__ import annotations

from typing import Final

EVIDENCE_LADDER: Final[tuple[dict[str, object], ...]] = (
    {"level": 1, "id": "digital", "label": "DIGITAL", "symbol": "🟣", "meaning": "synthetic Digital Twin result", "physical_claim": False},
    {"level": 2, "id": "testbed", "label": "TESTBED", "symbol": "🧪", "meaning": "controlled authorised hardware experiment", "physical_claim": False},
    {"level": 3, "id": "measured", "label": "MEASURED", "symbol": "📡", "meaning": "calibrated authorised physical measurement", "physical_claim": True},
    {"level": 4, "id": "verified", "label": "VERIFIED", "symbol": "🟢", "meaning": "repeatably demonstrated capability under defined conditions", "physical_claim": True},
    {"level": 5, "id": "field", "label": "FIELD", "symbol": "🌍", "meaning": "demonstrated in an authorised real-world operating environment", "physical_claim": True},
    {"level": 6, "id": "resilient", "label": "RESILIENT", "symbol": "🛡️", "meaning": "meets defined requirements through failure, interference, degradation and recovery tests", "physical_claim": True},
    {"level": 7, "id": "certified", "label": "CERTIFIED", "symbol": "💎", "meaning": "evidence package passed the stated OAP certification and governance protocol", "physical_claim": True},
)

CERTIFICATION_TRUTH: Final[str] = (
    "OAP Certified means certified under the stated OAP protocol only; it does not "
    "imply regulator, standards-body or accredited third-party certification."
)

GUARDIAN_SEMANTIC_LOCKS: Final[tuple[str, ...]] = (
    "motion_is_not_identity",
    "presence_is_not_identity",
    "presence_is_not_intrusion",
    "intrusion_signal_is_not_motive",
    "simulation_is_not_measurement",
)

PRIVACY_EVIDENCE_FIELDS: Final[tuple[str, ...]] = (
    "raw_rf_egress",
    "raw_video_egress",
    "biometric_identification",
    "persistent_person_tracking",
    "matrix_minimisation",
    "retention_policy",
    "authorisation",
)

CERTIFICATE_FIELDS: Final[tuple[str, ...]] = (
    "capability",
    "hardware",
    "software",
    "environment",
    "test_methodology",
    "measurements",
    "accuracy",
    "false_positive_rate",
    "false_negative_rate",
    "latency",
    "privacy_boundary",
    "failure_tests",
    "known_limitations",
    "evidence_provenance",
    "verification_date",
    "version",
    "human_authority",
)


def evidence_status() -> dict[str, object]:
    return {
        "canonical": True,
        "levels": EVIDENCE_LADDER,
        "separate_dimensions": ("evidence_class", "confidence", "action_authority"),
        "guardian_semantic_locks": GUARDIAN_SEMANTIC_LOCKS,
        "privacy_evidence_fields": PRIVACY_EVIDENCE_FIELDS,
        "certificate_fields": CERTIFICATE_FIELDS,
        "certification_truth": CERTIFICATION_TRUTH,
        "human_authority_final": True,
    }
