"""MATRIX-001: real Flask route proof; not Matrix simulation output.

Uses the repository's existing app and pytest fixtures. Deliberately does not
assume every 404 is a broken route: some private paths intentionally conceal
their existence. This suite never grants permissions or mutates production.
"""
from __future__ import annotations

import pytest


UNKNOWN_PUBLIC_PATH = "/matrix-proof-this-route-must-not-exist-7f3d9a"


@pytest.mark.parametrize("fixture_name", ("client", "anonymous_client"))
def test_matrix_001_unknown_public_route_returns_real_404(request, fixture_name):
    """Tank: exercise the real Flask request stack, not run_simulation()."""
    test_client = request.getfixturevalue(fixture_name)
    response = test_client.get(UNKNOWN_PUBLIC_PATH, follow_redirects=False)
    assert response.status_code == 404
    assert response.data.strip(), "404 must not render a blank response"
    assert response.headers.get("Location") is None, "404 must not redirect"


@pytest.mark.parametrize("fixture_name", ("client", "anonymous_client"))
def test_matrix_001_existing_public_world_remains_available(request, fixture_name):
    """Trinity: a valid public route must not regress during 404 recovery work."""
    test_client = request.getfixturevalue(fixture_name)
    response = test_client.get("/world", follow_redirects=False)
    assert response.status_code == 200
    assert response.data.strip(), "public front door must not render blank"


def test_matrix_001_simulated_training_never_counts_as_execution():
    """Oracle: advisory simulation receipts cannot certify real test execution."""
    from mission_control import matrix_simulation

    result = matrix_simulation.run_simulation("MATRIX-001", mode="route")
    assert result["state"] == "simulated_for_review"
    assert result["execution_granted"] is False
    assert result["external_action_taken"] is False
    assert result["founder_final_required"] is True
