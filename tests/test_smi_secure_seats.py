"""Founder-gated SMI seat placements cannot activate or impersonate agents."""
from __future__ import annotations

from mission_control import agents, smi_secure_seats
from mission_control import civic_judiciary_candidates as civic
from mission_control import specialist_agent_candidates as draft
from mission_control import specialist_command_candidates as expanded


def test_every_registered_and_candidate_agent_has_distinct_seat():
    p = smi_secure_seats.board()
    assert p["checks_passed"] is True, p["errors"]
    assert p["placed_existing_agents"] == 78
    assert p["reserved_new_candidates"] == 84
    assert p["total_expected"] == 162
    assert p["seat_placement_coverage_percent"] == 100.0
    original = [seat for family in p["existing_families"] for seat in family["seats"]]
    proposed = [seat for branch in p["branches"] for seat in branch["candidate_seats"]]
    assert len(original) == 78
    assert len(proposed) == 84
    assert len({s["seat_key"] for s in (*original, *proposed)}) == 162
    assert {s["name"] for s in original} == {
        s["name"] for s in agents.AGENT_REGISTRY
    }
    assert {s["name"] for s in proposed} == {
        s["name"] for s in (*draft.PROPOSED_AGENTS, *expanded.EXTENDED_AGENTS,
                             *civic.COURT_AND_GOVERNMENT_AGENTS)
    }


def test_all_twelve_branches_and_seven_existing_families_present():
    p = smi_secure_seats.board()
    assert len(p["branches"]) == 12
    assert len(p["existing_families"]) == 7
    assert all(branch["candidate_seats"] for branch in p["branches"])
    assert sum(len(b["candidate_seats"]) for b in p["branches"]) == 84
    assert sum(len(b["seats"]) for b in p["existing_families"]) == 78


def test_candidate_seats_never_grant_execution_votes_or_login():
    p = smi_secure_seats.board()
    assert p["checks_passed"] is True
    assert p["new_agents_activated"] == p["new_agent_passports_issued"] == 0
    assert p["live_readiness_percent"] is None
    assert p["overall_vpi_percent"] is None
    assert p["independent_votes_recorded"] is False
    assert p["safeguards"]["issues_credentials"] is False
    assert p["safeguards"]["human_authority_final"] is True
    for branch in p["branches"]:
        for seat in branch["candidate_seats"]:
            assert seat["status"] == "reserved_review_only"
            assert seat["identity_ref"] is None
            assert seat["permissions_granted"] is False
            assert seat["passport_issued_by_seat"] is False
            assert seat["vote_from_seat_allowed"] is False
            assert seat["execution_from_seat_allowed"] is False


def test_real_offices_chess_pieces_and_guardian_system_are_not_agent_seats():
    p = smi_secure_seats.board()
    refs = p["reference_positions"]
    assert refs["chess_pieces"] == (
        "King", "Queen", "Rook", "Bishop", "Knight", "Pawn"
    )
    assert len(refs["government_offices"]) == 2
    assert refs["protected_governance_stations"] == (
        "Guardian", "Aegis", "Green Gate", "HRM"
    )
    all_names = {s["name"] for family in p["existing_families"]
                 for s in family["seats"]}
    all_names |= {s["name"] for branch in p["branches"]
                  for s in branch["candidate_seats"]}
    assert "Guardian" not in all_names
    assert "Emperor" not in all_names
    assert "President" not in all_names


def test_fail_closed_if_duplicate_candidate_is_inserted():
    bad = (list(draft.PROPOSED_AGENTS) + list(expanded.EXTENDED_AGENTS)
           + list(civic.COURT_AND_GOVERNMENT_AGENTS))
    bad[-1] = dict(bad[0])
    p = smi_secure_seats.board(proposed_agents=bad)
    assert p["checks_passed"] is False
    assert "duplicate_seat_keys" in p["errors"]
    assert p["branches"] == ()
    assert p["existing_families"] == ()
    assert p["seat_placement_coverage_percent"] is None


def test_fail_closed_if_injected_candidate_is_privileged():
    bad = (list(draft.PROPOSED_AGENTS) + list(expanded.EXTENDED_AGENTS)
           + list(civic.COURT_AND_GOVERNMENT_AGENTS))
    bad[0] = {**bad[0], "execution_enabled": True, "permissions": ("EXECUTE",)}
    p = smi_secure_seats.board(proposed_agents=bad)
    assert p["checks_passed"] is False
    assert "privileged_or_invalid_seat" in p["errors"]
    assert p["branches"] == ()


def test_fail_closed_if_existing_agent_count_is_changed():
    p = smi_secure_seats.board(canonical_agents=agents.AGENT_REGISTRY[:-1])
    assert p["checks_passed"] is False
    assert "registry_population_invalid" in p["errors"]
    assert p["existing_families"] == ()



def test_21_court_and_21_civic_seats_preserve_separation_of_powers():
    p = smi_secure_seats.board()
    assert p["checks_passed"] is True
    assert p["new_court_research_seats"] == 21
    assert p["new_civic_research_seats"] == 21
    refs = p["reference_positions"]
    assert refs["court_agents_are_not_real_judges"] is True
    assert refs["political_agents_are_nonpartisan_research_only"] is True
    assert {"US", "UK", "Ghana"} == set(refs["constitutional_relations"])
    assert "judiciary" in refs["civic_independent_powers"]
    branch_keys = {branch["key"] for branch in p["branches"]}
    assert {"court_process", "legal_rights", "constitutional",
            "local_accountability"} <= branch_keys


def test_political_targeting_or_fake_court_power_blocks_all_seats():
    bad = (list(draft.PROPOSED_AGENTS) + list(expanded.EXTENDED_AGENTS)
           + list(civic.COURT_AND_GOVERNMENT_AGENTS))
    bad[-1] = {**bad[-1], "election_persuasion_enabled": True}
    p = smi_secure_seats.board(proposed_agents=bad)
    assert p["checks_passed"] is False
    assert "privileged_or_invalid_seat" in p["errors"]
    assert p["branches"] == ()
    bad[-1] = {**bad[-1], "election_persuasion_enabled": False,
               "court_order_enabled": True}
    p = smi_secure_seats.board(proposed_agents=bad)
    assert p["checks_passed"] is False
    assert p["existing_families"] == ()


def test_private_founder_only_routes_and_no_write(client):
    page = client.get("/mission/war-room/secure-seats")
    data = client.get("/mission/war-room/secure-seats/status")
    assert page.status_code == 200
    assert data.status_code == 200
    assert "no-store" in page.headers["Cache-Control"]
    assert "no-store" in data.headers["Cache-Control"]
    assert "SMI Secure Seats" in page.get_data(as_text=True)
    assert "Reserved for review only" in page.get_data(as_text=True)
    assert "84" in page.get_data(as_text=True)
    assert data.get_json()["checks_passed"] is True
    assert data.get_json()["new_agents_activated"] == 0
    assert client.post("/mission/war-room/secure-seats").status_code == 405


def test_anonymous_secure_seat_routes_fail_closed(anonymous_client):
    response = anonymous_client.get("/mission/war-room/secure-seats/status")
    assert response.status_code == 401
    assert "no-store" in response.headers["Cache-Control"]
    assert "reserved_new_candidates" not in response.get_data(as_text=True)
    assert anonymous_client.get("/mission/war-room/secure-seats").status_code == 302


def test_nonfounder_secure_seat_routes_rejected(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda _user: False)
    response = client.get("/mission/war-room/secure-seats/status")
    assert response.status_code == 403
    assert "human_authority_required" in response.get_data(as_text=True)
    assert "reserved_new_candidates" not in response.get_data(as_text=True)
    assert client.get("/mission/war-room/secure-seats").status_code == 403


def test_route_metadata_marks_founder_only_and_api(client):
    from mission_control import views

    assert views.secure_seat_board._oap_founder_only is True
    assert views.secure_seat_board_status._oap_founder_only is True
    assert views.secure_seat_board_status._oap_api is True
