from mission_control import ecosystem_intelligence


def _signal(
    domain: str,
    summary: str,
    *,
    postcode: str,
    borough: str = "Merton",
    region: str = "Greater London",
    pressure: int = 50,
    truth_state: str = "observed",
    horizon: str = "now",
    affected_systems: tuple[str, ...] = (),
    risk: str = "",
    opportunity: str = "",
    recommendation: str = "",
) -> dict[str, object]:
    return {
        "domain": domain,
        "summary": summary,
        "pressure": pressure,
        "confidence": 88,
        "truth_state": truth_state,
        "horizon": horizon,
        "source": "governed_runtime_test",
        "evidence": (f"proof:{domain}:{postcode}",),
        "geography": {
            "postcode": postcode,
            "borough_district": borough,
            "county_region": region,
            "country": "United Kingdom",
            "continent": "Europe",
        },
        "affected_systems": affected_systems,
        "risk": risk,
        "opportunity": opportunity,
        "recommendation": recommendation,
    }


def test_deep_status_is_system_not_agent_and_keeps_authority_boundary():
    current = ecosystem_intelligence.status()

    assert current["classification"] == "intelligence_system_not_agent"
    assert current["hierarchy"][0] == "Human Authority"
    assert current["hierarchy"][1] == "SMI"
    assert current["hierarchy"][2] == "Ecosystem Intelligence"
    assert len(current["domains"]) == 10
    assert current["time_horizons"] == ("now", "next", "trend")
    assert current["truth_states"] == ("observed", "inferred", "forecast", "confirmed")
    assert current["privacy_default"] == "aggregate_contextual_not_individual_surveillance"
    assert current["extended_matrix_roles_status"] == "passport_review_only"
    assert current["execution_granted"] is False
    assert current["human_authority"] == "final"


def test_cross_postcode_learning_detects_borough_pattern_without_claiming_cause():
    signals = (
        _signal("movement", "CR4 journey delay", postcode="CR4", pressure=68),
        _signal("movement", "SW16 journey delay", postcode="SW16", pressure=66),
        _signal("risk", "SW17 fulfilment pressure", postcode="SW17", pressure=63),
    )

    pattern = ecosystem_intelligence.cross_postcode_learning(signals)

    assert pattern["cross_postcode"] is True
    assert pattern["distinct_postcodes"] == 3
    assert pattern["pattern_scope"] == "borough_district"
    assert pattern["cause_confirmed"] is False
    assert pattern["execution_granted"] is False


def test_analysis_builds_low_noise_founder_pack_and_rsi_candidate():
    result = ecosystem_intelligence.analyse(
        (
            _signal(
                "nature",
                "Heavy rain increasing local pressure",
                postcode="CR4",
                pressure=72,
                affected_systems=("Nature", "Movement"),
                risk="Road conditions may reduce ETA reliability",
            ),
            _signal(
                "movement",
                "Journey times are degrading",
                postcode="SW16",
                pressure=84,
                truth_state="confirmed",
                affected_systems=("Movement", "Booking", "Market"),
                recommendation="Prepare an approved alternate route",
            ),
            _signal(
                "opportunity",
                "Local fulfilment capacity may be useful",
                postcode="SW17",
                pressure=62,
                truth_state="forecast",
                horizon="next",
                affected_systems=("Market", "Booking"),
                opportunity="Additional local fulfilment capacity",
            ),
        ),
        scope="South London",
        pressure_scores={
            "demand": 76,
            "movement": 84,
            "environmental": 72,
            "recovery_capacity": 48,
        },
    )

    founder = result["founder_view"]
    handoff = ecosystem_intelligence.recursive_improvement_handoff(result)

    assert result["state"] == "high"
    assert result["war_room_required"] is True
    assert result["human_authority_required"] is True
    assert result["geographic_pattern"]["cross_postcode"] is True
    assert founder["state"] == "high"
    assert founder["weakest_link"]["domain"] == "movement"
    assert set(founder["affected_systems"]) == {"Nature", "Movement", "Booking", "Market"}
    assert founder["forecast"] == ("Local fulfilment capacity may be useful",)
    assert founder["risk"] == ("Road conditions may reduce ETA reliability",)
    assert founder["opportunity"] == ("Additional local fulfilment capacity",)
    assert founder["human_authority_required"] is True
    assert founder["execution_granted"] is False
    assert handoff["eligible"] is True
    assert handoff["proposal_created"] is False
    assert handoff["automatic_deploy_allowed"] is False


def test_dashboard_never_invents_current_ecosystem_values(client):
    response = client.get("/mission/intelligence/ecosystem")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Awaiting real signal pack" in page
    assert "does not invent weather" in page
    assert "Human Authority remains final" in page
    assert response.headers["Cache-Control"] == "no-store"


def test_founder_analysis_api_uses_explicit_signals_and_does_not_execute(client):
    response = client.post(
        "/mission/intelligence/ecosystem/analyse",
        json={
            "scope": "Mitcham",
            "signals": [
                _signal("place", "Local demand rising", postcode="CR4", pressure=44),
                _signal("movement", "Booking pressure rising", postcode="CR4", pressure=58),
            ],
            "pressure_scores": {"demand": 61, "movement": 58},
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["scope"] == "Mitcham"
    assert payload["cross_domain"] is True
    assert payload["execution_granted"] is False
    assert payload["matrix_signal"]["sender"] == "Trinity"
    assert payload["founder_view"]["execution_granted"] is False
    assert response.headers["Cache-Control"] == "no-store"
