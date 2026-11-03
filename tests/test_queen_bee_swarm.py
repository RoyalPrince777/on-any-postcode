"""Queen Bee swarm plans remain bounded proposals without execution."""
import pytest

from oap.smi.queen_bee_swarm import SwarmTask, plan_swarm


def task(name="research", dependencies=()):
    return SwarmTask(name, "akan_core", "Koradaso", "heritage_research", ("public_records",), dependencies)


def test_no_distributed_work_means_no_assignment():
    plan = plan_swarm((task(),))
    assert not plan.assignments and not plan.honey_receipts
    assert plan.advisory_only and not plan.authority_granted and not plan.workers_started


def test_bounded_assignments_keep_family_ownership():
    plan = plan_swarm((task(), task("verify", ("research",))), distributed_work=True)
    assert len(plan.assignments) == 2
    assert plan.family_ownership_unchanged and not plan.authority_granted
    assert plan.honey_receipts == ("honey:planned:research", "honey:planned:verify")


@pytest.mark.parametrize("tasks", [
    (task(), task()),
    (task("research", ("research",)),),
    (task("research", ("missing",)),),
    (SwarmTask("", "akan_core", "Koradaso", "research"),),
])
def test_reject_invalid_assignments(tasks):
    with pytest.raises(ValueError):
        plan_swarm(tasks, distributed_work=True)
