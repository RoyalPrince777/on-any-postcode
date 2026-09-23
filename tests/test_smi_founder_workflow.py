"""Private SMI Founder continuity / War Room contract; no tool execution."""
from mission_control import oap_inference_gateway as gateway
from mission_control import smi_chat_runtime_core as core
from mission_control import smi_founder_workflow as workflow

HISTORY = [
    {"role": "user", "content": "Review the OAP Civilization OS with the War Room."},
    {"role": "assistant", "content": "War Room architecture review: evidence is incomplete; no runtime Green Gate."},
]


def test_purple_continues_supplied_war_room_at_depth_21():
    turn = workflow.resolve_turn("🟣", HISTORY)
    assert turn["intent"] == "CONTINUE_CURRENT_MISSION"
    assert turn["review_may_continue"] is True
    assert turn["war_room_requested"] is True
    assert turn["preferred_depth"] == 21
    assert turn["execution_granted"] is False


def test_purple_without_context_cannot_invent_mission():
    turn = workflow.resolve_turn("🟣", [])
    assert turn["history_has_mission_context"] is False
    assert turn["review_may_continue"] is False
    assert turn["war_room_requested"] is False


def test_green_is_review_approval_not_execution_or_proof():
    turn = workflow.resolve_turn("🟢", HISTORY)
    assert turn["intent"] == "FOUNDER_DESIGN_APPROVAL"
    assert turn["design_approval_is_execution_authority"] is False
    assert turn["production_status_requires_runtime_evidence"] is True
    assert turn["execution_granted"] is False


def test_manual_selector_is_not_overridden_by_purple():
    turn = workflow.resolve_turn("🟣 smi 21", HISTORY, requested_mode="manual")
    assert turn["preferred_depth"] is None
    assert turn["war_room_requested"] is True
    assert turn["execution_granted"] is False


def test_seven_judges_26_lenses_7x_use_existing_canonical_sources():
    status = workflow.status()
    assert status["judge_names"] == (
        "Shere Khan", "Bagheera", "Agent Smith", "Lion",
        "Morpheus", "Akela", "Owl",
    )
    assert len(status["lens_ids"]) == 26
    assert status["seven_x"] == (
        "Discovery", "Verification", "Alternatives", "Adversarial",
        "Systems", "Consequence", "Synthesis",
    )
    assert status["seven_star"] == (
        "Truth", "Function", "Security", "Stability",
        "Integration", "Compliance", "Learning",
    )


def test_private_local_and_bridge_prompt_receive_flags():
    turn = workflow.resolve_turn("🟣", HISTORY)
    messages = gateway._local_messages(
        "🟣", HISTORY, {"founder_workflow": turn}, [],
        code_mode=False,
    )
    assert "CONTINUE_CURRENT_MISSION" in messages[0]["content"]
    assert "FOUNDER WORKFLOW" in messages[0]["content"]
    assert messages[-1]["content"] == "🟣"
    assert "execution_granted" in messages[0]["content"]


def test_public_inference_never_receives_private_founder_workflow():
    messages = gateway._public_messages(
        "hello", [], {"founder_workflow": workflow.resolve_turn("🟣", HISTORY)},
        code_mode=False,
    )
    assert "FOUNDER WORKFLOW" not in messages[0]["content"]
    assert "CONTINUE_CURRENT_MISSION" not in messages[0]["content"]


def test_existing_mode_remains_manual_and_war_room_remains_21():
    manual = core._auto_runtime_mode("🟣 smi 21", requested_level="manual",
                                     studio_mode=False, code_mode=False,
                                     image_attached=False)
    war = core._auto_runtime_mode("War Room", requested_level="war_room",
                                  studio_mode=False, code_mode=False,
                                  image_attached=False)
    assert manual[0] == "manual" and manual[2] == 3
    assert war[0] == "deep_dive" and war[2] == 21


def test_paired_purple_green_continues_only_known_mission():
    turn = workflow.resolve_turn("🟣🟢", HISTORY)
    assert turn["intent"] == "CONTINUE_WITH_FOUNDER_DESIGN_APPROVAL"
    assert turn["review_may_continue"] is True
    assert turn["war_room_requested"] is True
    assert turn["design_approval_requires_identifiable_context"] is True
    assert turn["explicit_execution_approval_received"] is False
    assert turn["execution_granted"] is False


def test_paired_signal_without_context_does_not_invent_approval_subject():
    turn = workflow.resolve_turn("🟢 🟣", [])
    assert turn["intent"] == "CONTINUE_WITH_FOUNDER_DESIGN_APPROVAL"
    assert turn["history_has_mission_context"] is False
    assert turn["review_may_continue"] is False
    assert turn["execution_granted"] is False


def test_assistant_alone_never_proves_mission_context():
    history = [
        {"role": "assistant", "content": "War Room result: choose a new mission."},
        {"role": "user", "content": "🟣"},
    ]
    turn = workflow.resolve_turn("🟣", history)
    assert turn["history_has_mission_context"] is False
    assert turn["war_room_requested"] is False


def test_new_founder_topic_cannot_inherit_old_war_room_mode():
    changed = [
        *HISTORY,
        {"role": "user", "content": "Let's write a short birthday caption."},
        {"role": "assistant", "content": "Caption prepared; older War Room notes remain."},
    ]
    turn = workflow.resolve_turn("🟣", changed)
    assert turn["history_has_mission_context"] is True
    assert turn["war_room_requested"] is False
    assert turn["preferred_depth"] is None


def test_latest_founder_war_room_mission_still_resumes():
    changed = [
        {"role": "user", "content": "First, write a birthday caption."},
        {"role": "assistant", "content": "Caption prepared."},
        *HISTORY,
    ]
    turn = workflow.resolve_turn("🟣", changed)
    assert turn["review_may_continue"] is True
    assert turn["war_room_requested"] is True
    assert turn["preferred_depth"] == 21
