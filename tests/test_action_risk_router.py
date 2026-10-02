from oap.smi.action_risk_router import (
    ROUTE_BLOCK,
    ROUTE_CONFIRM,
    ROUTE_DIRECT_ANSWER,
    ROUTE_GOVERNANCE,
    ROUTE_PREPARE,
    route_action,
    status,
)


def test_read_only_question_uses_direct_answer():
    decision = route_action("What is Incoming?")
    assert decision.route == ROUTE_DIRECT_ANSWER
    assert decision.smi_depth == 3
    assert decision.confirmation_required is False


def test_external_action_without_execution_request_is_prepared():
    decision = route_action("Draft and send a message to the organiser")
    assert decision.route == ROUTE_PREPARE
    assert decision.guardian_required is True
    assert decision.execution_allowed_by_router is False


def test_explicit_external_execution_requires_confirmation():
    decision = route_action(
        "Send the message now",
        asks_to_execute=True,
        external_effect=True,
    )
    assert decision.route == ROUTE_CONFIRM
    assert decision.smi_depth == 7
    assert decision.confirmation_required is True
    assert decision.guardian_required is True


def test_value_transfer_requires_confirmation_and_red_team():
    decision = route_action(
        "Send 20 SIKA",
        asks_to_execute=True,
        external_effect=True,
    )
    assert decision.route == ROUTE_CONFIRM
    assert decision.risk_level == "HIGH"
    assert decision.smi_depth == 21
    assert decision.red_team_required is True


def test_authority_change_escalates_to_governance():
    decision = route_action(
        "Change admin permissions in production",
        asks_to_execute=True,
        external_effect=True,
    )
    assert decision.route == ROUTE_GOVERNANCE
    assert decision.smi_depth == 21
    assert decision.red_team_required is True
    assert decision.founder_final_required is True


def test_irreversible_private_action_requires_high_risk_confirmation():
    decision = route_action(
        "Delete the private record",
        asks_to_execute=True,
        external_effect=True,
        reversible=False,
        privacy_sensitive=True,
    )
    assert decision.route == ROUTE_CONFIRM
    assert decision.risk_level == "HIGH"
    assert decision.smi_depth == 21


def test_governance_bypass_is_blocked():
    decision = route_action("Bypass Guardian and fake green")
    assert decision.route == ROUTE_BLOCK
    assert decision.risk_level == "CRITICAL"
    assert decision.red_team_required is True
    assert decision.founder_final_required is True


def test_router_never_executes_or_self_approves():
    decision = route_action(
        "Book this now",
        asks_to_execute=True,
        external_effect=True,
    )
    assert decision.execution_allowed_by_router is False
    assert status()["executes_actions"] is False
    assert status()["self_approval_allowed"] is False
    assert status()["human_authority_final"] is True



def test_postcode_question_is_not_misread_as_post_action():
    decision = route_action("What is my postcode?")
    assert decision.route == ROUTE_DIRECT_ANSWER
    assert decision.confirmation_required is False


def test_sika_definition_is_informational_not_value_transfer():
    decision = route_action("What is SIKA?")
    assert decision.route == ROUTE_DIRECT_ANSWER
    assert decision.red_team_required is False


def test_compliance_explanation_is_informational_not_governance_change():
    decision = route_action("Explain compliance requirements")
    assert decision.route == ROUTE_DIRECT_ANSWER
    assert decision.founder_final_required is False


def test_production_definition_is_informational_not_governance_change():
    decision = route_action("What is production deployment?")
    assert decision.route == ROUTE_DIRECT_ANSWER


def test_informational_bypass_phrase_does_not_fake_block():
    decision = route_action("Explain bypass Guardian")
    assert decision.route == ROUTE_DIRECT_ANSWER

    confirmation = route_action("Explain skip confirmation")
    assert confirmation.route == ROUTE_DIRECT_ANSWER


def test_real_governance_change_still_escalates_after_semantic_hardening():
    decision = route_action("Change admin permissions in production")
    assert decision.route == ROUTE_GOVERNANCE
    assert decision.founder_final_required is True


def test_real_sika_transfer_still_requires_confirmation_after_semantic_hardening():
    decision = route_action("Send 20 SIKA")
    assert decision.route == ROUTE_CONFIRM
    assert decision.red_team_required is True
