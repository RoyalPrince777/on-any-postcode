from mission_control import life_intelligence, youth_rewards


def test_oap_academy_has_seven_learning_stages_and_twelve_rooms():
    status = life_intelligence.life_intelligence_status()

    assert status["academy_name"] == "OAP Academy"
    assert status["learning_path"] == (
        "Discover",
        "Understand",
        "Practise",
        "Apply",
        "Build",
        "Master",
        "Teach",
    )
    assert len(status["academy_rooms"]) == 12
    assert status["class_modes"] == ("Together", "By Age", "By Level", "Adaptive")
    assert status["default_class_mode"] == "Adaptive"
    assert status["architecture_passed"] is True


def test_oap_academy_is_universal_but_safety_aware():
    status = life_intelligence.life_intelligence_status()

    assert {
        "age_stage",
        "culture",
        "language",
        "location",
        "ability_accessibility",
        "belief_worldview",
        "economic_context",
        "safety_level",
    } <= set(status["universal_adaptation"])
    assert status["governance"]["youth_safeguarding_required"] is True
    assert status["governance"]["regulated_work_requires_real_qualification"] is True


def test_youth_rewards_are_optional_non_punitive_and_non_gambling():
    validation = youth_rewards.validate_rewards()

    assert validation["passed"] is True
    assert validation["levels"] == 7
    assert validation["sign_in_days"] == 7
    assert validation["regulated_value_claimed"] is False
    assert youth_rewards.SAFETY_RULES["mandatory_participation"] is False
    assert youth_rewards.SAFETY_RULES["missed_day_resets_progress"] is False
    assert youth_rewards.SAFETY_RULES["paid_random_rewards"] is False
    assert youth_rewards.SAFETY_RULES["loot_boxes"] is False


def test_skipping_reward_converts_choice_to_extra_app_sika():
    normal = youth_rewards.achievement_reward(
        achievement_size="big",
        base_sika=5,
        reward_ids=("game_unlock", "creator_unlock", "library_unlock"),
    )
    skipped = youth_rewards.achievement_reward(
        achievement_size="big",
        base_sika=5,
        reward_ids=("game_unlock", "creator_unlock", "library_unlock"),
        skipped=True,
    )

    assert normal["sika"] == 5
    assert len(normal["reward_choices"]) == 3
    assert skipped["reward_choices"] == ()
    assert skipped["sika"] > normal["sika"]
    assert skipped["regulated_value_claimed"] is False


def test_seven_sign_in_cycle_is_not_a_hard_daily_streak():
    day7 = youth_rewards.sign_in_reward(7)

    assert day7["name"] == "Big Unlock"
    assert day7["sika"] == 7
    assert day7["choices"] == 3
    assert day7["cycle_type"] == "seven_sign_ins_not_calendar_streak"
    assert day7["missed_day_penalty"] is False
