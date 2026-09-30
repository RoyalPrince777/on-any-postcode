from flask import Flask

from mission_control import all_in_ai_views


def test_all_in_ai_route_registers_founder_command_surface():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/mission/all-in-ai" in rules
    assert "/mission/all-in-ai/app" in rules
    assert "/mission/all-in-ai/mission" in rules
    assert "/mission/all-in-ai/mission/latest" in rules
    assert "/mission/all-in-ai/mission/<mission_id>" in rules
    assert "/mission/all-in-ai/mission/<mission_id>/inference/<request_id>" in rules
    assert "/mission/all-in-ai/mission/<mission_id>/stop" in rules
    assert "/mission/all-in-ai/mission/<mission_id>/recover" in rules
    assert "/mission/all-in-ai/mission/<mission_id>/action-handoff" in rules
    assert "/mission/all-in-ai/mission/<mission_id>/execute-internal-record" in rules
    assert "/mission/all-in-ai/mission/<mission_id>/rollback-internal-record" in rules


def test_all_in_ai_route_is_not_public():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    response = app.test_client().get("/mission/all-in-ai")
    assert response.status_code in {401, 403}


def test_all_in_ai_mission_route_is_not_public():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    response = app.test_client().post(
        "/mission/all-in-ai/mission",
        json={"mission": "test"},
    )
    assert response.status_code in {401, 403}


def test_all_in_ai_lifecycle_routes_are_not_public():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    mission = "00000000-0000-0000-0000-000000000002"
    client = app.test_client()
    assert client.get("/mission/all-in-ai/mission/latest").status_code in {401, 403}
    assert client.get(f"/mission/all-in-ai/mission/{mission}").status_code in {401, 403}
    assert client.get(f"/mission/all-in-ai/mission/{mission}/inference/{mission}").status_code in {401, 403}
    assert client.post(
        f"/mission/all-in-ai/mission/{mission}/stop",
        json={"expected_previous_hash": "a" * 64},
    ).status_code in {401, 403}
    assert client.post(
        f"/mission/all-in-ai/mission/{mission}/recover",
        json={"expected_previous_hash": "b" * 64},
    ).status_code in {401, 403}
    assert client.post(
        f"/mission/all-in-ai/mission/{mission}/action-handoff",
        json={
            "reviewed_request_id": "00000000-0000-0000-0000-000000000003",
            "action_name": "SYNC_INTERNAL_RECORD",
        },
    ).status_code in {401, 403}
    assert client.post(
        f"/mission/all-in-ai/mission/{mission}/execute-internal-record",
        json={
            "reviewed_request_id": "00000000-0000-0000-0000-000000000003",
            "record_id": "00000000-0000-0000-0000-000000000004",
            "expected_status": "draft",
            "target_status": "active",
        },
    ).status_code in {401, 403}
    assert client.post(
        f"/mission/all-in-ai/mission/{mission}/rollback-internal-record",
        json={
            "reviewed_request_id": "00000000-0000-0000-0000-000000000005",
            "rollback_token": {
                "record_id": "00000000-0000-0000-0000-000000000004",
                "expected_status": "active",
                "target_status": "draft",
                "before_hash": "a" * 64,
                "after_hash": "b" * 64,
            },
        },
    ).status_code in {401, 403}


def test_all_in_ai_app_route_is_not_public():
    app = Flask(__name__)
    app.secret_key = "test"

    @app.get("/enter", endpoint="auth_page")
    def auth_page():
        return "login"

    app.register_blueprint(all_in_ai_views.bp, url_prefix="/mission")
    response = app.test_client().get("/mission/all-in-ai/app")
    assert response.status_code == 302
    assert "/enter" in response.headers["Location"]


def test_captain_mission_keeper_restores_only_independently_verified_latest():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1]
        / "mission_control" / "templates" / "all_in_ai.html"
    ).read_text(encoding="utf-8")
    assert 'id="restore" type="button"' in template
    assert "all_in_ai.all_in_ai_mission_latest" in template
    assert "await loadVerifiedMission(latest.mission_id,latest)" in template
    assert "expected.version!==receipt?.version" in template
    assert "expected.state!==receipt?.state" in template
    assert "receipt.mission_id===missionId" in template
    for proof in (
        "receipt.read_back_verified===true",
        "receipt.audit_verified===true",
        "receipt.hrm_verified===true",
        "receipt.execution_granted===false",
        "receipt.approval_granted===false",
        "receipt.human_authority_final===true",
    ):
        assert proof in template
    assert "if(!showReceipt(" in template
    assert "proofVerified=false;latestDigest=null;latestState=null" in template


def test_captain_checkpoint_digest_is_never_trusted_from_browser_session():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1]
        / "mission_control" / "templates" / "all_in_ai.html"
    ).read_text(encoding="utf-8")
    assert "persistCheckpoint();" in template
    assert "showReceipt('🛑 STOP durably recorded.',body.receipt)" in template
    assert "showReceipt('♻️ Mission recovered for review. No execution granted.',body.receipt)" in template
    assert "if(!proofVerified||!latestDigest)return;" in template
    assert "sessionStorage.getItem(sessionPrefix+'digest')" not in template
    assert "Never trust sessionStorage digest for STOP/recovery" in template



def test_captain_inference_inspector_reuses_private_read_only_route():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1]
        / "mission_control" / "templates" / "all_in_ai.html"
    ).read_text(encoding="utf-8")
    assert 'id="inference-inspect" type="button" disabled' in template
    assert "inferenceButton.addEventListener('click',async()=>{" in template
    assert "'/inference/'+encodeURIComponent(requestId)" in template
    assert "if(!proofVerified||!missionId||latestState==='stopped')return;" in template
    assert "evidence?.mission_id!==inspectedMission" in template
    assert "evidence?.request_id!==requestId" in template
    for field in (
        "mission_checkpoint_verified",
        "mission_text_hash_matched",
        "governed_response_recorded",
    ):
        assert "evidence?." + field + "!==true" in template
    for field in (
        "inference_route_attested",
        "first_party_inference_proven",
        "mission_execution_proven",
        "execution_granted",
        "approval_granted",
    ):
        assert "evidence?." + field + "!==false" in template
    assert "evidence?.human_authority_final!==true" in template
    assert "Independent worker attestation: NOT PROVEN" in template
    assert "Mission execution: NOT PROVEN" in template
    assert "inferenceResult.textContent=[" in template
    assert "inferenceResult.innerHTML" not in template
