from mission_control import company_evidence_ingestion


def test_missing_evidence_fails_closed_to_unknown():
    snapshot = company_evidence_ingestion.ingest_snapshot(())

    assert snapshot["valid_evidence_count"] == 0
    assert snapshot["all_domains_proven"] is False
    assert snapshot["company_registry_proven"] is False
    assert snapshot["music_evidence_ready"] is False
    assert snapshot["pod_evidence_ready"] is False
    assert snapshot["commercial_evidence_ready"] is False
    assert set(snapshot["unresolved_domains"]) == set(company_evidence_ingestion.DOMAINS)
    assert snapshot["full_green"] is False


def test_latest_valid_evidence_wins_per_domain():
    snapshot = company_evidence_ingestion.ingest_snapshot(
        (
            {
                "domain": "company_registry",
                "state": "STALE",
                "source_reference": "registry-old",
                "observed_at": "2026-09-01T00:00:00+00:00",
            },
            {
                "domain": "company_registry",
                "state": "PROVEN",
                "source_reference": "registry-current",
                "authority_reference": "official-registry",
                "observed_at": "2026-10-02T12:00:00+00:00",
            },
        )
    )

    state = snapshot["states"]["company_registry"]
    assert state["state"] == "PROVEN"
    assert state["source_reference"] == "registry-current"
    assert snapshot["company_registry_proven"] is True


def test_invalid_or_unattributed_items_do_not_turn_green():
    snapshot = company_evidence_ingestion.ingest_snapshot(
        (
            {
                "domain": "artist_rights",
                "state": "PROVEN",
                "source_reference": "",
                "observed_at": "2026-10-02T12:00:00+00:00",
            },
            {
                "domain": "not-a-domain",
                "state": "PROVEN",
                "source_reference": "x",
                "observed_at": "2026-10-02T12:00:00+00:00",
            },
        )
    )

    assert snapshot["valid_evidence_count"] == 0
    assert snapshot["invalid_evidence_count"] == 2
    assert snapshot["music_evidence_ready"] is False


def test_music_and_pod_require_complete_relevant_evidence():
    evidence = (
        {
            "domain": "artist_rights",
            "state": "PROVEN",
            "source_reference": "rights-receipt",
            "observed_at": "2026-10-02T12:00:00+00:00",
        },
        {
            "domain": "music_catalogue",
            "state": "PROVEN",
            "source_reference": "catalogue-receipt",
            "observed_at": "2026-10-02T12:00:00+00:00",
        },
        {
            "domain": "clothing_supplier",
            "state": "PROVEN",
            "source_reference": "supplier-clothing",
            "observed_at": "2026-10-02T12:00:00+00:00",
        },
        {
            "domain": "print_on_demand_supplier",
            "state": "PROVEN",
            "source_reference": "supplier-pod",
            "observed_at": "2026-10-02T12:00:00+00:00",
        },
        {
            "domain": "pricing_margin",
            "state": "PROVEN",
            "source_reference": "margin-proof",
            "observed_at": "2026-10-02T12:00:00+00:00",
        },
    )
    snapshot = company_evidence_ingestion.ingest_snapshot(evidence)

    assert snapshot["music_evidence_ready"] is True
    assert snapshot["pod_evidence_ready"] is True
    assert snapshot["commercial_evidence_ready"] is False
    assert snapshot["all_domains_proven"] is False
    assert snapshot["full_green"] is False


def test_evidence_never_grants_legal_or_execution_authority():
    snapshot = company_evidence_ingestion.ingest_snapshot(
        {
            "domain": domain,
            "state": "PROVEN",
            "source_reference": f"proof-{domain}",
            "authority_reference": "reviewed-source",
            "observed_at": "2026-10-02T12:00:00+00:00",
        }
        for domain in company_evidence_ingestion.DOMAINS
    )

    assert snapshot["all_domains_proven"] is True
    assert snapshot["evidence_presence_is_not_legal_authority"] is True
    assert snapshot["evidence_presence_is_not_rights_adjudication"] is True
    assert snapshot["evidence_presence_is_not_regulatory_permission"] is True
    assert snapshot["external_action_taken"] is False
    assert snapshot["founder_final_required"] is True
    assert snapshot["full_green"] is False
