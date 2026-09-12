import mission_control.smi_brain_evidence_runner as smi_brain_evidence_runner
import mission_control.smi_judge_rotation as smi_judge_rotation


EXPECTED_JUDGES = (
    "Shere Khan",
    "Bagheera",
    "Agent Smith",
    "Lion",
    "Morpheus",
    "Akela",
    "Owl",
)


def _receipt_ok(*args, **kwargs):
    return {
        "ok": True,
        "read_back_ok": True,
        "receipt_id": "test-war-room-receipt",
        "receipt_kind": "war_room_live_proof_receipt",
    }


def test_canonical_seven_judges_are_not_replaced_by_gates_or_recovery():
    status = smi_judge_rotation.status()

    assert status["canonical_count"] == 7
    assert status["canonical_judges"] == EXPECTED_JUDGES
    assert status["separate_gates"] == ("Guardian", "Green Gate")
    assert status["recovery_witness"] == "Neo"
    assert status["all_judges_present"] is True
    assert "Guardian" not in status["canonical_judges"]
    assert "Green Gate" not in status["canonical_judges"]
    assert "Neo" not in status["canonical_judges"]
    assert status["full_green"] is False


def test_rotation_keeps_all_seven_while_rotating_focus():
    plans = tuple(
        smi_judge_rotation.rotation_plan(scope=scope, command="war_room")
        for scope in ("amygdala", "brainstem", "hippocampus", "all")
    )

    for plan in plans:
        assert len(plan["review_order"]) == 7
        assert set(plan["review_order"]) == set(EXPECTED_JUDGES)
        assert plan["rotation_focus"] in ("Morpheus", "Akela", "Owl")
        assert plan["all_judges_present"] is True

    assert len({plan["rotation_focus"] for plan in plans}) >= 2


def test_all_seven_rule_lenses_run_and_local_receipt_does_not_claim_full_green(
    monkeypatch,
):
    monkeypatch.setattr(
        smi_judge_rotation.smi_receipt_backend,
        "write_receipt",
        _receipt_ok,
    )

    review = smi_judge_rotation.run_review(
        scope="amygdala",
        command="war_room",
        evidence_current=4,
        local_receipt_green=False,
        neon_mirror_green=False,
    )

    assert review["reviewed_count"] == 7
    assert tuple(result["judge"] for result in review["judge_results"]) == EXPECTED_JUDGES
    assert review["receipt_ok"] is True
    assert review["review_complete_local"] is True
    assert review["neon_mirror_green"] is False
    assert review["founder_final_required"] is True
    assert review["full_green"] is False
    assert "Shere Khan" in review["holds"]
    assert "Lion" in review["holds"]
    assert "Morpheus" in review["holds"]


def test_evidence_runner_reports_canonical_review_truthfully(monkeypatch):
    monkeypatch.setattr(
        smi_judge_rotation.smi_receipt_backend,
        "write_receipt",
        _receipt_ok,
    )

    result = smi_brain_evidence_runner.run(
        part="amygdala",
        gate="4",
        command="war_room",
    )

    assert result["judge_review"]["canonical_judges"] == EXPECTED_JUDGES
    assert result["judge_review"]["reviewed_count"] == 7
    assert result["top_bar"]["judges"] == "7 / 7 CANONICAL REVIEWED"
    assert result["top_bar"]["guardian"] == "🛡 REQUIRED · SEPARATE GATE"
    assert result["top_bar"]["green_gate"] == "🟢 REQUIRED · SEPARATE GATE"
    assert result["top_bar"]["neo"] == "RECOVERY WITNESS"
    assert result["full_green"] is False
