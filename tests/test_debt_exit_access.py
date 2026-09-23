"""No-write access seam tests: mock web identity; no live auth certification."""
from __future__ import annotations

import pytest

from mission_control import debt_exit_access as access
from mission_control.debt_exit_truth import Action, TransitionDenied, new_case

OWNER = "owner_0001"
CASE = "case_00001"


class Identity:
    identity_id = OWNER


class FakeIdentityEngine:
    def validate(self, principal):
        if principal != OWNER:
            raise PermissionError("identity unavailable")
        return Identity()


class Decision:
    def __init__(self, allowed):
        self.allowed = allowed


class FakePermissionEngine:
    def __init__(self, allowed=True):
        self.allowed = allowed

    def authorize_identity(self, identity, required_permission):
        assert required_permission == "DEBT_EXIT_REVIEW"
        return Decision(self.allowed)


def guarded(monkeypatch, *, member=True, allowed=True, guardian=True,
            owner=OWNER, version=0, recovery=False):
    monkeypatch.setattr(access.web_security, "current_authenticated_user",
                        lambda: {"id": OWNER, "recovery_founder": recovery} if member else None)
    monkeypatch.setattr(access.web_security, "authenticated_identity", lambda: OWNER)
    loads = []

    def load(case_id):
        loads.append(case_id)
        return new_case(CASE, owner)

    def guard(principal, case_id, action):
        return guardian

    try:
        proposal = access.propose_debt_change(
            CASE, Action.DISPUTE, identity_engine=FakeIdentityEngine(),
            permission_engine=FakePermissionEngine(allowed),
            load_trusted_case=load, guardian_review=guard, expected_version=version,
            evidence_ref="record_0001",
        )
        return proposal, loads
    except TransitionDenied:
        assert not loads or (member and allowed and guardian and not recovery)
        raise


def test_review_only_no_storage_hrm_or_financial_execution(monkeypatch):
    proposed, loads = guarded(monkeypatch)
    assert loads == [CASE]
    assert proposed.case.disputed
    assert proposed.persisted is False
    assert proposed.hrm_recorded is False
    assert proposed.financially_executed is False


@pytest.mark.parametrize("opts", [
    {"member": False}, {"allowed": False}, {"guardian": False},
    {"recovery": True}, {"owner": "owner_0002"}, {"version": 1},
])
def test_fails_closed_for_unauthorised_or_stale(monkeypatch, opts):
    with pytest.raises(TransitionDenied):
        guarded(monkeypatch, **opts)


def test_invalid_request_rejected_before_case_load(monkeypatch):
    monkeypatch.setattr(access.web_security, "current_authenticated_user",
                        lambda: {"id": OWNER})
    monkeypatch.setattr(access.web_security, "authenticated_identity", lambda: OWNER)
    def unexpected_load(_):
        raise AssertionError("must not load case")
    with pytest.raises(TransitionDenied, match="invalid_request"):
        access.propose_debt_change(
            "bad", Action.DISPUTE, identity_engine=FakeIdentityEngine(),
            permission_engine=FakePermissionEngine(),
            load_trusted_case=unexpected_load,
            guardian_review=lambda *_: True, expected_version=0,
        )


def test_guardian_unavailability_rejects_before_load(monkeypatch):
    monkeypatch.setattr(access.web_security, "current_authenticated_user",
                        lambda: {"id": OWNER})
    monkeypatch.setattr(access.web_security, "authenticated_identity", lambda: OWNER)
    def unavailable(*_):
        raise RuntimeError("private guardian error")
    with pytest.raises(TransitionDenied, match="guardian_unavailable"):
        access.propose_debt_change(
            CASE, Action.DISPUTE, identity_engine=FakeIdentityEngine(),
            permission_engine=FakePermissionEngine(),
            load_trusted_case=lambda _: pytest.fail("must not load case"),
            guardian_review=unavailable, expected_version=0,
        )
