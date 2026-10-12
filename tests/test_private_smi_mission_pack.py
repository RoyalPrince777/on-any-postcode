"""Mission-pack projection cannot grant authority or alter permanent families."""
from oap.smi.private_mission_pack import private_smi_mission_pack


def test_founder_pack_contains_distinct_critical_roles():
    pack = private_smi_mission_pack()
    names = [name for name, _ in pack.roles]
    assert len(names) == len(set(names))
    assert {"Gorilla", "Fox", "Neo", "Agent Smith", "Guardian"} <= set(names)
    assert pack.advisory_only and not pack.authority_granted
    assert not pack.runtime_verified
    assert pack.permanent_wolf_pack_unchanged and pack.matrix_core_unchanged


def test_queen_bee_only_for_distributed_work():
    local = private_smi_mission_pack()
    distributed = private_smi_mission_pack(distributed_work=True)
    assert "Queen Bee" not in [name for name, _ in local.roles]
    assert "Queen Bee" in [name for name, _ in distributed.roles]
    assert distributed.queen_bee_assigned
    assert not local.queen_bee_assigned


def test_no_runtime_or_authority_from_distributed_assignment():
    pack = private_smi_mission_pack(distributed_work=True)
    assert not pack.runtime_verified and not pack.authority_granted
