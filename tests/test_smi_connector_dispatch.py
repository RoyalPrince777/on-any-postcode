import pytest

from mission_control import smi_connector_dispatch as dispatcher


@pytest.mark.parametrize("tool", ["smi_status", "studio_capabilities"])
def test_unauthenticated_tool_is_denied(tool):
    with pytest.raises(dispatcher.ConnectorAccessDenied, match="founder_authentication_required"):
        dispatcher.dispatch(tool, {}, authenticated_founder=False)


@pytest.mark.parametrize("tool", ["studio_generate", "studio_cancel", "publish", "deploy", "studio_projects", "../status", "", None])
def test_unapproved_tools_are_denied(tool):
    with pytest.raises(dispatcher.ConnectorAccessDenied, match="connector_tool_not_allowed"):
        dispatcher.dispatch(tool, {}, authenticated_founder=True)


def test_arguments_cannot_expand_access():
    with pytest.raises(ValueError, match="connector_arguments_must_be_empty"):
        dispatcher.dispatch("smi_status", {"execute": True}, authenticated_founder=True)


def test_allowlisted_response_never_reveals_sensitive_fields():
    result = dispatcher.dispatch(
        "smi_status", {}, authenticated_founder=True,
        studio_status={
            "id": "oap-studio-intelligence",
            "generation_backend_proven": False,
            "full_live_certificate": False,
            "token": "private-credential",
            "founder_notes": "private-data",
        },
    )
    assert result["studio_declared"] is True
    assert result["generation_backend_proven"] is False
    assert result["execution_granted"] is False
    assert "private-credential" not in str(result)
    assert "private-data" not in str(result)


def test_capability_tool_stays_read_only_and_no_false_live_claims():
    result = dispatcher.dispatch(
        "studio_capabilities", {}, authenticated_founder=True,
        studio_status={"id": "oap-studio-intelligence"},
    )
    assert result["studio_declared"] is True
    assert result["full_live_certificate"] is False
    assert result["publishing_granted"] is False
    assert result["execution_granted"] is False
