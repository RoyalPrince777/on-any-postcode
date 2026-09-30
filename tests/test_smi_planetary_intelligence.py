from oap.smi import planetary_intelligence


def _signal(postcode, country, pressure=30, truth_state="observed"):
    return {
        "domain": "nature",
        "horizon": "now",
        "truth_state": truth_state,
        "summary": f"Weather context for {postcode}",
        "source": "authorised-test-source",
        "evidence": (f"receipt:{postcode}",),
        "pressure": pressure,
        "confidence": 80,
        "geography": {
            "postcode": postcode,
            "country": country,
            "continent": "Europe",
        },
        "affected_systems": ("OAP Nature",),
    }


def test_status_reuses_existing_intelligence_and_keeps_authority_locked():
    state = planetary_intelligence.status()
    assert state["observation_ladder_level"] == 6
    assert state["earth_intelligence_reused"] is True
    assert state["ecosystem_intelligence_reused"] is True
    assert state["network_calls_made"] is False
    assert state["universal_surveillance"] is False
    assert state["execution_granted"] is False
    assert state["approval_granted"] is False
    assert state["human_authority_final"] is True
    assert state["full_planetary_runtime_ready"] is False


def test_correlate_preserves_local_to_global_truth_without_claiming_causation():
    result = planetary_intelligence.correlate((
        _signal("SW16 1AA", "United Kingdom"),
        _signal("SE15 1AA", "United Kingdom", truth_state="confirmed"),
    ))
    assert result["represented_levels"] == ("postcode", "country", "continent")
    assert result["geographic_pattern"]["cross_postcode"] is True
    assert result["geographic_pattern"]["cause_confirmed"] is False
    assert result["truth_mix"]["observed"] == 1
    assert result["truth_mix"]["confirmed"] == 1
    assert result["network_calls_made"] is False
    assert result["execution_granted"] is False
    assert result["full_planetary_runtime_ready"] is False


def test_correlate_rejects_unattributed_unproven_or_unknown_geography_inputs():
    missing_source = _signal("SW16 1AA", "United Kingdom")
    missing_source["source"] = ""
    try:
        planetary_intelligence.correlate((missing_source,))
    except ValueError as exc:
        assert "source" in str(exc)
    else:
        raise AssertionError("missing source must fail closed")

    missing_evidence = _signal("SW16 1AA", "United Kingdom")
    missing_evidence["evidence"] = ()
    try:
        planetary_intelligence.correlate((missing_evidence,))
    except ValueError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("missing evidence must fail closed")

    unsupported = _signal("SW16 1AA", "United Kingdom")
    unsupported["geography"]["universe"] = "Milky Way"
    try:
        planetary_intelligence.correlate((unsupported,))
    except ValueError as exc:
        assert "Unsupported planetary geography" in str(exc)
    else:
        raise AssertionError("unsupported geography must fail closed")