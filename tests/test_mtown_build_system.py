"""Regression coverage for MBS — M Town Build System."""
from mission_control import earth_is_our_turf
from mission_control import mtown_build_system


def test_mbs_status_contract():
    state=mtown_build_system.status()
    assert state["name"]=="M Town Build System"
    assert state["tiers"]==["LIVE","BACKGROUND","MEMORY"]


def test_mbs_marks_current_chunk_live():
    world=earth_is_our_turf.public_state(earth_is_our_turf.new_world())
    mbs=world["mbs"]
    assert mbs["active_chunk"]=="central"
    assert mbs["tiers"]["central"]=="LIVE"
    assert mbs["truth"]["real_world_geometry_claimed"] is False
    assert mbs["unreal_handoff"]["world_partition"] is True
    assert mbs["unreal_handoff"]["authoritative_truth"]=="oap_world_state"


def test_mbs_preloads_route_chunks_without_loading_everything_live():
    state=earth_is_our_turf.new_world()
    state=earth_is_our_turf.action(
        state,
        command="navigate",
        target="phipps-bridge",
        mode="car",
    )
    world=earth_is_our_turf.public_state(state)
    mbs=world["mbs"]
    assert mbs["tiers"]["central"]=="LIVE"
    assert "lavender" in mbs["preload_next"] or "phipps" in mbs["preload_next"]
    assert sum(1 for tier in mbs["tiers"].values() if tier=="LIVE")==1
    assert any(tier=="MEMORY" for tier in mbs["tiers"].values())


def test_mbs_manifest_is_deterministic_for_same_world_state():
    state=earth_is_our_turf.public_state(earth_is_our_turf.new_world())
    first=state["mbs"]["manifest_id"]
    second=earth_is_our_turf.public_state(earth_is_our_turf.new_world())["mbs"]["manifest_id"]
    assert first==second
