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
    assert "if(missionMutationPending||actionPending||!proofVerified||!latestDigest)return;" in template
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
    assert "if(actionPending||missionMutationPending||!proofVerified||!missionId||latestState==='stopped')return;" in template
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



def test_captain_review_action_gate_never_executes_or_extents_authority():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1]
        / "mission_control" / "templates" / "all_in_ai.html"
    ).read_text(encoding="utf-8")
    assert 'id="handoff-review" type="button" disabled' in template
    assert "handoffButton.addEventListener('click',async()=>{" in template
    assert "if(actionPending||missionMutationPending||!proofVerified||!missionId||latestState==='stopped')return;" in template
    assert "'/action-handoff'" in template
    assert "method:'POST'" in template
    assert "body:JSON.stringify({reviewed_request_id:requestId,action_name:'SYNC_INTERNAL_RECORD'})" in template
    assert "latestDigest!==reviewedDigest" in template
    for check in (
        "gate?.mission_id!==reviewedMission",
        "gate?.reviewed_request_id!==requestId",
        "gate?.action_name!=='SYNC_INTERNAL_RECORD'",
        "gate?.mission_receipt_verified!==true",
        "gate?.execution_performed!==false",
        "gate?.authority_transferred!==false",
        "gate?.human_authority_final!==true",
        "body?.execution_performed!==false",
        "body?.human_authority_final!==true",
    ):
        assert check in template
    assert "gate.status==='AUTHORIZED_NOT_EXECUTED'&&gate.execution_authorized===true" in template
    assert "gate.execution_authorized===false" in template
    assert "Review does not execute; the separate bounded Founder control requires fresh server-side governance." in template
    assert "handoffResult.textContent=" in template
    assert "handoffResult.innerHTML" not in template
    assert "'/execute-internal-record'" in template
    assert "'/rollback-internal-record'" in template


def test_captain_checkpoint_change_invalidates_previous_handoff_display():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1]
        / "mission_control" / "templates" / "all_in_ai.html"
    ).read_text(encoding="utf-8")
    assert "handoffResult.textContent='Checkpoint updated. Review governance again if needed.'" in template
    assert "handoffResult.textContent='Mission proof cleared. Governed action must be reviewed again.'" in template



def test_red_team_request_epoch_blocks_stale_mission_results_and_parallel_mutation():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1]
        / "mission_control" / "templates" / "all_in_ai.html"
    ).read_text(encoding="utf-8")
    assert "let missionEpoch=0;" in template
    assert "let missionMutationPending=false;" in template
    assert "missionEpoch+=1;" in template
    assert "if(missionEpoch!==startedEpoch)return false;" in template
    assert "if(missionEpoch!==restoreEpoch)return;" in template
    assert "if(missionEpoch===readEpoch)" in template
    assert "missionEpoch!==inspectedEpoch" in template
    assert "latestDigest!==inspectedDigest" in template
    assert "missionEpoch!==reviewedEpoch" in template
    assert "latestDigest!==reviewedDigest" in template
    assert "if(missionMutationPending||actionPending||!proofVerified||!latestDigest)return;" in template
    assert "missionMutationPending=true;updateControls();" in template
    assert "finally{missionMutationPending=false;updateControls();}" in template
    assert "startButton.disabled=busy;" in template
    assert "restoreButton.disabled=busy;" in template
    assert "readButton.disabled=busy||!missionId;" in template
    assert "inferenceButton.disabled=busy||" in template
    assert "handoffButton.disabled=busy||" in template


def test_red_team_action_review_does_not_expose_internal_authorization(monkeypatch):
    from flask import Flask

    from mission_control import all_in_ai_views

    app = Flask(__name__)
    app.secret_key = "test"
    mission_id = "00000000-0000-0000-0000-000000000002"
    request_id = "00000000-0000-0000-0000-000000000003"
    monkeypatch.setattr(all_in_ai_views, "_require_csrf", lambda: None)
    monkeypatch.setattr(all_in_ai_views, "_founder_id", lambda: "founder-id")
    monkeypatch.setattr(
        all_in_ai_views.all_in_ai_action_bridge,
        "handoff_status",
        lambda *_a, **_k: {
            "mission_id": mission_id,
            "reviewed_request_id": request_id,
            "status": "AUTHORIZED_NOT_EXECUTED",
            "action_name": "SYNC_INTERNAL_RECORD",
            "execution_authorized": True,
            "execution_performed": False,
            "human_authority_final": True,
            "authority_transferred": False,
            "authorization": {
                "approval_receipt_id": "internal-only", "signal_id": "secret",
            },
            "review": {"content_hash": "internal-review"},
            "action_policy": {"external": False},
        },
    )
    with app.test_request_context(
        f"/all-in-ai/mission/{mission_id}/action-handoff",
        method="POST",
        json={"reviewed_request_id": request_id},
    ):
        # Exercise the real route body, bypassing only the login decorator.
        response = all_in_ai_views.all_in_ai_action_handoff.__wrapped__(mission_id)
        payload = response.get_json()
        assert response.status_code == 200
        assert payload["execution_performed"] is False
        assert payload["human_authority_final"] is True
        assert payload["result"]["status"] == "AUTHORIZED_NOT_EXECUTED"
        assert payload["result"]["execution_authorized"] is True
        for private_field in ("authorization", "review", "action_policy"):
            assert private_field not in payload["result"]
        assert "internal-only" not in response.get_data(as_text=True)
        assert "internal-review" not in response.get_data(as_text=True)



def test_captain_protected_execution_requires_current_governance_and_strict_outcome():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1] / "mission_control"
        / "templates" / "all_in_ai.html"
    ).read_text(encoding="utf-8")
    assert 'id="internal-execute" type="button" disabled' in template
    assert 'id="internal-rollback" type="button" disabled' in template
    assert "executeButton.addEventListener('click',async()=>{" in template
    assert "readyHandoff={missionId:reviewedMission,digest:reviewedDigest," in template
    assert "gate.epoch!==missionEpoch" in template
    assert "actionPending=true;readyHandoff=null;rollbackEvidence=null;" in template
    assert "'/execute-internal-record'" in template
    assert "action?.action_name==='SYNC_INTERNAL_RECORD'" in template
    assert "result?.execution_evidence_state==='VERIFIED'" in template
    assert "result?.outcome_receipt_verified===true" in template
    assert "result?.automatic_retry_allowed===false" in template
    assert "action?.external_side_effect===false" in template
    assert "action?.financial_side_effect===false" in template
    assert "validDigest(token?.before_hash)&&validDigest(token?.after_hash)" in template
    assert "RECONCILIATION REQUIRED" in template


def test_captain_rollback_requires_fresh_human_request_and_never_autoretries():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1] / "mission_control"
        / "templates" / "all_in_ai.html"
    ).read_text(encoding="utf-8")
    assert "rollbackButton.addEventListener('click',async()=>{" in template
    assert "freshRequest===evidence.executeRequestId" in template
    assert "'/rollback-internal-record'" in template
    assert "rollbackEvidence=null;updateControls();" in template
    assert "result?.rollback_verified===true&&body?.rollback_verified===true" in template
    assert "recovery?.after_hash===evidence.token.before_hash" in template
    assert "Do not blindly retry." in template
    assert "sessionStorage.setItem(sessionPrefix+'rollback" not in template
    assert "localStorage.setItem(" not in template
