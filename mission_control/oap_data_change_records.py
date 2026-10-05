"""Canonical OAP Data change-record model for governed code changes.

This module does not fetch GitHub, approve merges, deploy code, or invent proof.
It only normalises evidence already supplied by governed callers.
"""
from collections.abc import Iterable
from dataclasses import asdict, dataclass


ALLOWED_GATE_STATES = {
    "GREEN",
    "BUILDING",
    "LOCKED",
    "PRIVATE",
    "NEEDS_APPROVAL",
    "STALE",
    "UNCERTAIN",
    "BLOCKED",
}


@dataclass(frozen=True)
class OapDataChangeRecord:
    oap_data_id: str
    mission: str
    system: str
    before: str
    after: str
    files_changed: tuple[str, ...]
    routes_functions_affected: tuple[str, ...]
    tests_run: tuple[str, ...]
    security_checks: tuple[str, ...]
    runtime_proof: tuple[str, ...]
    rollback_point: str
    claw_test: str
    green_gate: str
    merge_commit: str | None = None
    deployment_digest: str | None = None
    truth_boundary: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _clean_many(values: Iterable[object]) -> tuple[str, ...]:
    return tuple(
        value
        for value in (str(item).strip() for item in values)
        if value
    )


def build_change_record(
    *,
    oap_data_id: object,
    mission: object,
    system: object,
    before: object,
    after: object,
    files_changed: Iterable[object] = (),
    routes_functions_affected: Iterable[object] = (),
    tests_run: Iterable[object] = (),
    security_checks: Iterable[object] = (),
    runtime_proof: Iterable[object] = (),
    rollback_point: object,
    claw_test: object,
    green_gate: object,
    merge_commit: object | None = None,
    deployment_digest: object | None = None,
    truth_boundary: Iterable[object] = (),
) -> OapDataChangeRecord:
    gate = str(green_gate).strip().upper()
    if gate not in ALLOWED_GATE_STATES:
        raise ValueError("invalid_green_gate_state")

    required = {
        "oap_data_id": str(oap_data_id).strip(),
        "mission": str(mission).strip(),
        "system": str(system).strip(),
        "before": str(before).strip(),
        "after": str(after).strip(),
        "rollback_point": str(rollback_point).strip(),
        "claw_test": str(claw_test).strip(),
    }
    if any(not value for value in required.values()):
        raise ValueError("missing_required_oap_data_field")

    return OapDataChangeRecord(
        oap_data_id=required["oap_data_id"],
        mission=required["mission"],
        system=required["system"],
        before=required["before"],
        after=required["after"],
        files_changed=_clean_many(files_changed),
        routes_functions_affected=_clean_many(routes_functions_affected),
        tests_run=_clean_many(tests_run),
        security_checks=_clean_many(security_checks),
        runtime_proof=_clean_many(runtime_proof),
        rollback_point=required["rollback_point"],
        claw_test=required["claw_test"],
        green_gate=gate,
        merge_commit=(str(merge_commit).strip() or None) if merge_commit is not None else None,
        deployment_digest=(str(deployment_digest).strip() or None)
        if deployment_digest is not None
        else None,
        truth_boundary=_clean_many(truth_boundary),
    )


def certification_state(record: OapDataChangeRecord) -> str:
    """Return evidence-bound certification state without promoting missing proof."""
    if record.green_gate != "GREEN":
        return record.green_gate
    if not record.tests_run or not record.runtime_proof or not record.rollback_point:
        return "UNCERTAIN"
    if not record.merge_commit:
        return "NEEDS_APPROVAL"
    return "CERTIFIED"


def status() -> dict[str, object]:
    return {
        "name": "OAP Data Change Records",
        "canonical": True,
        "mutates_repository": False,
        "approves_changes": False,
        "deploys": False,
        "green_gate_states": tuple(sorted(ALLOWED_GATE_STATES)),
        "required_evidence": (
            "mission",
            "before_after",
            "tests",
            "runtime_proof",
            "rollback_point",
            "claw_test",
            "green_gate",
        ),
    }
