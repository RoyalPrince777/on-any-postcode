"""Production-foundation regression coverage for EARTH IS OUR TURF."""
from pathlib import Path

import eiot_world_server
from mission_control import earth_is_our_turf, mtown_endless_world, mtown_world_server


def test_endless_cells_are_deterministic_and_unbounded():
    a=mtown_endless_world.cell(x=250000,y=-250000,world_seed="mtown-v1")
    b=mtown_endless_world.cell(x=250000,y=-250000,world_seed="mtown-v1")
    c=mtown_endless_world.cell(x=250001,y=-250000,world_seed="mtown-v1")
    assert a==b
    assert a["seed"]!=c["seed"]
    assert a["exact_real_geometry_claimed"] is False
    assert mtown_endless_world.status()["unbounded_coordinates"] is True


def test_endless_ring_has_expected_cell_count():
    cells=mtown_endless_world.ring(center_x=0,center_y=0,radius=2)
    assert len(cells)==25
    assert len({(row["x"],row["y"]) for row in cells})==25


def test_persistence_status_distinguishes_capability_from_readiness(monkeypatch):
    monkeypatch.delenv("DATABASE_URL",raising=False)
    monkeypatch.delenv("OAP_PRIMARY_DATABASE_URL",raising=False)
    monkeypatch.delenv("OAP_PRIMARY_DATABASE_URL_B64",raising=False)
    status=__import__("mission_control.mtown_persistence",fromlist=["status"]).status()
    assert status["durable_supported"] is True
    assert status["durable_ready"] is False
    assert status["configured"] is False


def test_world_server_facade_is_authoritative():
    session=mtown_world_server.new_session()
    assert session["server"]["authoritative"] is True
    updated=mtown_world_server.act(session,command="help-local")
    assert updated["server"]["tick"]==1
    assert updated["world"]["player"]["influence"]==2
    earth_is_our_turf.public_state(updated["world"])


def test_dedicated_world_server_health_and_world_lifecycle():
    client=eiot_world_server.app.test_client()
    health=client.get("/healthz")
    assert health.status_code==200
    assert health.get_json()["authoritative"] is True
    created=client.post("/v1/worlds")
    assert created.status_code==201
    world_id=created.get_json()["world_id"]
    action=client.post(f"/v1/worlds/{world_id}/action",json={"command":"help-local"})
    assert action.status_code==200
    assert action.get_json()["server"]["tick"]==1
    cells=client.get("/v1/world/cells?x=99&y=-99&radius=1")
    assert cells.status_code==200
    assert len(cells.get_json()["cells"])==9


def test_unreal_project_and_dedicated_server_target_are_present():
    root=Path("unreal/EarthIsOurTurf")
    project=(root/"EarthIsOurTurf.uproject").read_text()
    server=(root/"Source/EarthIsOurTurfServer.Target.cs").read_text()
    bootstrap=(root/"Source/EarthIsOurTurf/EIOTWorldBootstrap.cpp").read_text()
    pedestrian=(root/"Source/EarthIsOurTurf/EIOTPedestrian.cpp").read_text()
    car=(root/"Source/EarthIsOurTurf/EIOTTrafficCar.cpp").read_text()
    assert '"EngineAssociation":"5.8"' in project
    assert "TargetType.Server" in server
    assert "/v1/world/cells" in bootstrap
    assert "AddMovementInput" in pedestrian
    assert "AddActorWorldOffset" in car
