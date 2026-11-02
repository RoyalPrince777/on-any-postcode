from mission_control import smi_auto


def test_named_agent_invocation_routes_exact_canonical_lenses():
    roles = smi_auto.explicit_review_roles(
        "Shere Khan do the Claw Test, then Neo and Owl review it."
    )
    assert roles == ("Neo", "Shere Khan", "Owl")


def test_auto_mode_uses_stable_review_pack_when_no_name_was_requested():
    roles = smi_auto.selected_review_roles("SMI review this", auto_mode=True)
    assert roles == (
        "Neo",
        "Shere Khan",
        "Bagheera",
        "Agent Smith",
        "Owl",
        "Guardian",
        "Green Gate",
    )


def test_explicit_name_augments_permanent_auto_core_pack():
    roles = smi_auto.selected_review_roles("Octopus and Fox review this", auto_mode=True)
    assert roles[:3] == ("Neo", "Shere Khan", "Bagheera")
    assert "Octopus" in roles
    assert "Fox" in roles


def test_manual_mode_uses_only_explicit_named_reviewers():
    roles = smi_auto.selected_review_roles("Spider review this", auto_mode=False)
    assert roles == ("Spider",)


def test_vote_board_is_evidence_classification_not_personality_simulation():
    board = smi_auto.build_evidence_vote_board(
        roles=("Neo", "Shere Khan", "Guardian"),
        brain={"passed": True, "high_impact": False},
        coherence={"passed": True},
        judgement={"constitution_consistent": True},
        guardian_outcome="PASSED",
    )
    assert board["summary"] == {"PASS": 3, "FAIL": 0, "CONDITIONAL": 0}
    assert board["authority_granted"] is False
    assert all(item["deterministic_evidence_review"] for item in board["votes"])
    assert not any(item["independent_personality_claimed"] for item in board["votes"])


def test_smi_v5_exposes_permanent_core_and_captain_auto_protocol():
    status = smi_auto.public_status()
    assert status["version"] == 6
    assert status["core_auto_review"] == ("Neo", "Shere Khan", "Bagheera")
    assert status["captain_auto_protocol"] == "SMI_FIRST_CORE_REVIEW_THEN_SPECIALISTS"


def test_octopus_spider_fox_are_canonical_review_lenses():
    roles = smi_auto.explicit_review_roles("Octopus Spider Fox")
    assert roles == ("Octopus", "Spider", "Fox")
    assert "systems integration" in smi_auto.review_lens("Octopus")
    assert "route mesh" in smi_auto.review_lens("Spider")
    assert "optimisation" in smi_auto.review_lens("Fox")


def test_shere_khan_full_authority_exceeds_claw_test_mode():
    lens = smi_auto.review_lens("Shere Khan")
    assert "threat intelligence" in lens
    assert "survivability authority" in lens
    assert "false-Green blocking" in lens
    assert "Claw Test is one pressure mode" in lens


def test_nirmata_aei_gorilla_recovery_review_is_coupled_without_authority():
    roles = smi_auto.selected_review_roles("Nirmata recover the build", auto_mode=True)
    assert all(role in roles for role in ("Nirmata", "AEI", "Gorilla"))
    assert len(roles) == len(set(roles))
    assert "rollback" in smi_auto.review_lens("Gorilla")
    assert smi_auto.selected_review_roles("Gorilla", auto_mode=False) == ("Gorilla",)
    board = smi_auto.build_evidence_vote_board(
        roles=("Nirmata", "AEI", "Gorilla"),
        brain={"passed": False, "high_impact": True},
        coherence={"passed": False},
        judgement={"constitution_consistent": False},
        guardian_outcome="BLOCKED",
    )
    assert board["summary"]["FAIL"] == 3
    assert board["authority_granted"] is False
    assert board["human_authority_final"] is True


def test_auto_swot_requires_verified_failed_build_logs():
    assert smi_auto.evidence_swot_for_failed_build({})["ready"] is False
    assert smi_auto.evidence_swot_for_failed_build({
        "ready": True, "log_analysis": {"ready": False}
    })["ready"] is False


def test_auto_swot_uses_only_verified_categories_without_granting_execution():
    data = {"ready": True, "log_analysis": {"ready": True, "log_categories": (
        {"job_id": 31, "categories": ("gradle_compile", "source_verification")},
    )}}
    result = smi_auto.evidence_swot_for_failed_build(data)
    assert result["ready"] is True
    assert result["weaknesses"] == ("gradle_compile", "source_verification")
    assert result["execution_granted"] is False
    assert result["approval_granted"] is False
    assert result["human_authority_final"] is True
    assert smi_auto.evidence_swot_for_failed_build({
        "ready": True, "log_analysis": {"ready": True, "log_categories": (
            {"job_id": 31, "categories": ("untrusted_input",)},
        )}
    })["ready"] is False
