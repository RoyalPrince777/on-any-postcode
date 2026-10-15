"""Read-only SMI alliance assurance protocol across OAP product domains.

Descriptive governance aid only: never launches agents, grants tool permissions,
or substitutes automated claims for observed CI/runtime evidence.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class AssuranceReview:
    domain: str
    expected: tuple[str, ...]
    observed: tuple[str, ...]
    missing: tuple[str, ...]
    contradictions: tuple[str, ...]
    verdict: str
    roles: tuple[tuple[str, str], ...]


ROLES = (
    ("gorilla", "Oversee Tank and Dozer; protect the last line of defence"),
    ("tank", "Preserve verified functioning capabilities"),
    ("dozer", "Remove blockers without weakening safety gates"),
    ("twin_one", "Specify expected, measurable evidence"),
    ("twin_two", "Independently compare actual evidence"),
    ("agent_smith", "Challenge assumptions and unsupported claims"),
    ("brown", "Investigate recurring defects"),
    ("jones", "Investigate conflicting evidence"),
    ("johnson", "Investigate stress and resilience limits"),
    ("jackson", "Investigate anomalies"),
    ("thompson", "Reject unsupported Green assertions"),
    ("shere_khan", "Adversarially attack the proof"),
)


def review_assurance(
    domain: str,
    expected: Mapping[str, bool],
    observed: Mapping[str, bool | None],
) -> AssuranceReview:
    """Return PASS only when every required condition has affirmative evidence.

    None/missing means unverified; False means contradictory observed evidence.
    Empty requirements are never sufficient for PASS.
    """
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("domain is required")
    if not expected or any(value is not True for value in expected.values()):
        raise ValueError("expected must contain affirmative required conditions")
    missing = tuple(sorted(key for key in expected if observed.get(key) is None))
    contradictions = tuple(sorted(key for key in expected if observed.get(key) is False))
    passed = not missing and not contradictions
    return AssuranceReview(
        domain=domain.strip(),
        expected=tuple(sorted(expected)),
        observed=tuple(sorted(key for key in expected if observed.get(key) is True)),
        missing=missing,
        contradictions=contradictions,
        verdict="PASS" if passed else "BLOCKED",
        roles=ROLES,
    )
