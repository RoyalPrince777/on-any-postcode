"""Regression tests for upgrade-only War Room agent ranking."""

from oap.war_room.agent_selection import (
    STABLE_REVIEW_CORE,
    score_agent,
    select_rotating_judges,
    status,
)


def _candidate(name, task_fit, evidence=90, outcome=90, dissent=80, consistency=90, recent=90):
    return {
        "name": name,
        "registry_status": "ACTIVE",
        "task_fit": task_fit,
        "performance": {
            "evidence_quality": evidence,
            "outcome_accuracy": outcome,
            "useful_dissent": dissent,
            "consistency": consistency,
            "recent_performance": recent,
        },
    }


def test_stable_core_keeps_locked_reviewers():
    assert STABLE_REVIEW_CORE == (
        "SMI First Look",
        "Shere Khan",
        "Bagheera",
        "Guardian",
        "Green Gate",
        "SMI Second Look",
        "Founder Final",
    )


def test_depth_seven_selects_best_fit_plus_challenger():
    result = select_rotating_judges(
        (
            _candidate("Akela", 97),
            _candidate("Architect", 95),
            _candidate("Neo", 80),
        ),
        task_domains=("governance",),
        depth=7,
    )

    assert result["selected"][0]["name"] == "Akela"
    assert result["selected"][1]["slot"] == "challenger"
    assert result["selected"][1]["name"] == "Architect"
    assert result["decision_authority"] is False
    assert result["human_authority_final"] is True


def test_depth_twenty_one_widens_rotating_judges():
    result = select_rotating_judges(
        (
            _candidate("Akela", 97),
            _candidate("Architect", 95),
            _candidate("Neo", 93),
            _candidate("Morpheus", 88),
            _candidate("Oracle", 85),
        ),
        task_domains=("architecture", "governance"),
        depth=21,
    )

    names = {item["name"] for item in result["selected"]}
    assert {"Akela", "Architect", "Neo"}.issubset(names)
    assert len(result["selected"]) >= 3


def test_unregistered_or_inactive_candidates_are_ignored():
    result = select_rotating_judges(
        (
            _candidate("Akela", 95),
            {
                **_candidate("Neo", 99),
                "registry_status": "PROPOSED",
            },
            _candidate("Invented Judge", 100),
        ),
        task_domains=("governance",),
        depth=21,
    )

    names = {item["name"] for item in result["ranked_candidates"]}
    assert names == {"Akela"}


def test_founder_correction_and_missed_risk_reduce_rank():
    baseline = score_agent(
        {
            "task_fit": 95,
            "evidence_quality": 95,
            "outcome_accuracy": 95,
            "useful_dissent": 95,
            "consistency": 95,
            "recent_performance": 95,
        }
    )
    penalised = score_agent(
        {
            "task_fit": 95,
            "evidence_quality": 95,
            "outcome_accuracy": 95,
            "useful_dissent": 95,
            "consistency": 95,
            "recent_performance": 95,
        },
        founder_correction_penalty=5,
        missed_risk_penalty=10,
    )

    assert penalised["score"] < baseline["score"]
    assert penalised["authority_effect"] == "none"


def test_domain_specific_score_overrides_generic_task_fit():
    result = select_rotating_judges(
        (
            {
                **_candidate("Architect", 60),
                "domain_scores": {"architecture": 99},
            },
            {
                **_candidate("Akela", 90),
                "domain_scores": {"architecture": 70},
            },
        ),
        task_domains=("architecture",),
        depth=7,
        challenger_slot=False,
    )

    assert result["selected"][0]["name"] == "Architect"


def test_status_is_upgrade_only_and_advisory():
    result = status()
    assert result["upgrade_only"] is True
    assert result["decision_authority"] is False
    assert result["human_authority_final"] is True
    assert result["challenger_slot"] is True
