from mission_control.agent_passport_audit import passport_reconciliation


def test_later_founder_decisions_are_reconciled_without_auto_registration():
    audit = passport_reconciliation()
    entries = {entry["name"]: entry for entry in audit["entries"]}
    assert entries["Mouse"]["decision"] == "restored"
    assert entries["Tigress"]["decision"] == "canonical_name"
    assert entries["Gorilla"]["decision"] == "approved_role"
    assert entries["Baloo"]["decision"] == "approved_role"
    assert entries["Lioness"]["decision"] == "approved_role"
    assert all(entry["passport_verified"] is False for entry in entries.values())
    assert all(entry["execution_authorised"] is False for entry in entries.values())
    assert audit["founder_final_required"] is True
    assert audit["production_green"] is False
