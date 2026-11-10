"""Youth Club reward rules for optional learning progression.

Rewards are achievement-linked, non-gambling and non-punitive. SIKA here is
an in-app reward representation only; this module does not create or promise
regulated money conversion.
"""

from __future__ import annotations

from typing import Any

REWARD_LEVELS = (
    "Spark",
    "Explorer",
    "Builder",
    "Creator",
    "Leader",
    "Mentor",
    "Legacy",
)

REWARD_FLOW = ("Learn", "Do", "Achieve", "Choose", "Unlock", "Enjoy")

REWARD_TYPES = (
    "game_unlock",
    "challenge_unlock",
    "creator_unlock",
    "library_unlock",
    "event_unlock",
    "mentor_unlock",
    "customisation",
    "sika_bonus",
)

CLAIM_ACTIONS = ("claim", "save", "swap_for_sika", "skip")

SIGN_IN_CYCLE: tuple[dict[str, object], ...] = (
    {"day":1,"name":"Tap In","sika":1,"choices":1},
    {"day":2,"name":"Still Here","sika":1,"choices":0},
    {"day":3,"name":"Building Momentum","sika":2,"choices":1},
    {"day":4,"name":"Halfway Boss","sika":2,"choices":1},
    {"day":5,"name":"Serious Now","sika":3,"choices":1},
    {"day":6,"name":"One More","sika":3,"choices":1},
    {"day":7,"name":"Big Unlock","sika":7,"choices":3},
)

SAFETY_RULES: dict[str, object] = {
    "mandatory_participation": False,
    "hard_daily_streak": False,
    "missed_day_resets_progress": False,
    "paid_random_rewards": False,
    "loot_boxes": False,
    "pay_to_progress": False,
    "public_sharing_required": False,
    "safety_security_can_override_access": True,
    "guardian_awareness_where_required": True,
    "regulated_money_conversion_promised": False,
}

def validate_rewards() -> dict[str, Any]:
    errors: list[str] = []
    if len(REWARD_LEVELS) != 7 or len(set(REWARD_LEVELS)) != 7:
        errors.append("Seven unique Youth Reward levels are required")
    if tuple(item["day"] for item in SIGN_IN_CYCLE) != tuple(range(1, 8)):
        errors.append("Sign-in cycle must be seven cumulative sign-ins")
    if any(int(item["sika"]) < 0 or int(item["choices"]) < 0 for item in SIGN_IN_CYCLE):
        errors.append("Reward values cannot be negative")
    if SAFETY_RULES["hard_daily_streak"] or SAFETY_RULES["missed_day_resets_progress"]:
        errors.append("Punitive streak mechanics are not allowed")
    if SAFETY_RULES["paid_random_rewards"] or SAFETY_RULES["loot_boxes"]:
        errors.append("Gambling-like reward mechanics are not allowed")
    if SAFETY_RULES["mandatory_participation"]:
        errors.append("Youth reward participation must stay optional")
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "levels": len(REWARD_LEVELS),
        "sign_in_days": len(SIGN_IN_CYCLE),
        "regulated_value_claimed": False,
    }


def achievement_reward(
    *,
    achievement_size: str,
    base_sika: int,
    reward_ids: tuple[str, ...] = (),
    skipped: bool = False,
) -> dict[str, object]:
    size = str(achievement_size).strip().casefold()
    choice_limits = {"small": 1, "big": 3, "milestone": 7}
    if size not in choice_limits:
        raise ValueError("unknown_achievement_size")
    if base_sika < 0:
        raise ValueError("invalid_sika")
    invalid = tuple(reward for reward in reward_ids if reward not in REWARD_TYPES)
    if invalid:
        raise ValueError("unknown_reward_type")
    limit = choice_limits[size]
    choices = tuple(reward_ids[:limit])
    skip_bonus = max(1, limit) if skipped else 0
    return {
        "achievement_size": size,
        "reward_choices": () if skipped else choices,
        "sika": base_sika + skip_bonus,
        "skipped_reward": skipped,
        "mandatory": False,
        "safety_override": True,
        "regulated_value_claimed": False,
    }


def sign_in_reward(sign_in_number: int) -> dict[str, object]:
    if not 1 <= int(sign_in_number) <= 7:
        raise ValueError("sign_in_number_must_be_1_to_7")
    reward = dict(SIGN_IN_CYCLE[int(sign_in_number) - 1])
    reward.update(
        {
            "cycle_type": "seven_sign_ins_not_calendar_streak",
            "missed_day_penalty": False,
            "mandatory": False,
        }
    )
    return reward
