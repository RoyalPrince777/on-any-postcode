"""SMI workbench naming projection must never imply live ballots or approval."""
from mission_control.smi_workbench import _naming_vote_workbench_projection


def test_naming_vote_workbench_preserves_founder_authority():
    vote = _naming_vote_workbench_projection()
    assert {"KORADASO", "ALL ENDZ", "KORAKWAN"}.issubset(vote["recovered_leaders"])
    assert vote["historical_wins"]["KORADASO"] == 3
    assert vote["advisory_only"] is True
    assert vote["founder_final_required"] is True
    assert vote["live_agent_ballots_verified"] is False
    assert vote["runtime_verified"] is False
    assert vote["persistent_ledger_ready"] is False
