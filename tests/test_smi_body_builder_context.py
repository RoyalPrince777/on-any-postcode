"""Body isolation: a Builder cannot execute a mismatched or unapproved plan."""
from dataclasses import replace

import pytest

from oap.contracts import ActionPlan, BuilderContext, action_plan_digest
from oap.kernel import BuilderRegistry


def test_builder_accepts_exact_human_approved_context():
    plan = ActionPlan(request_id="body-1", action_type="record_status", payload={"status": "reviewed"})
    context = BuilderContext(request_id=plan.request_id, receipt_id="receipt-1", identity_id="founder-1", authority_level=0, action_digest=action_plan_digest(plan))
    calls = []
    builder = BuilderRegistry()
    builder.register("record_status", lambda payload, approved: calls.append((payload, approved.receipt_id)))
    builder.execute(plan, context)
    assert calls == [({"status": "reviewed"}, "receipt-1")]


@pytest.mark.parametrize("mutation", [
    {"payload": {"status": "published"}},
    {"action_type": "another_action"},
    {"requires_human_approval": False},
])
def test_builder_rejects_plan_changes_without_invoking_handler(mutation):
    plan = ActionPlan(request_id="body-2", action_type="record_status", payload={"status": "reviewed"})
    context = BuilderContext(request_id=plan.request_id, receipt_id="receipt-2", identity_id="founder-1", authority_level=0, action_digest=action_plan_digest(plan))
    calls = []
    builder = BuilderRegistry()
    builder.register("record_status", lambda payload, approved: calls.append(payload))
    builder.register("another_action", lambda payload, approved: calls.append(payload))
    with pytest.raises(PermissionError):
        builder.execute(replace(plan, **mutation), context)
    assert calls == []


@pytest.mark.parametrize("mutation", [
    {"request_id": "different-request"},
    {"receipt_id": ""},
    {"identity_id": ""},
    {"authority_level": 1},
    {"action_digest": "0" * 64},
])
def test_builder_rejects_invalid_context_without_invoking_handler(mutation):
    plan = ActionPlan(request_id="body-3", action_type="record_status", payload={})
    context = BuilderContext(request_id=plan.request_id, receipt_id="receipt-3", identity_id="founder-1", authority_level=0, action_digest=action_plan_digest(plan))
    calls = []
    builder = BuilderRegistry()
    builder.register("record_status", lambda payload, approved: calls.append(payload))
    with pytest.raises(PermissionError):
        builder.execute(plan, replace(context, **mutation))
    assert calls == []
