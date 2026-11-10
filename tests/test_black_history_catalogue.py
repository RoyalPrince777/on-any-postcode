"""Black History review catalogue: historical uncertainty and privacy regression."""

from mission_control import black_history_catalogue


def test_cape_entry_keeps_date_dispute_and_citation_links():
    status = black_history_catalogue.catalogue_status()
    assert status["publication_enabled"] is False
    assert status["review_only"] is True
    entry = status["entries"][0]
    assert entry["review_status"] == "editorial_hold"
    assert entry["date_precision"] == "month"
    assert "25 or 27 October" in entry["date_uncertainty"]
    assert entry["coordinates"] is None
    assert len(entry["sources"]) >= 2
    assert all(source["url"].startswith("https://") for source in entry["sources"])


def test_review_entries_do_not_allow_mutating_source_records():
    first = black_history_catalogue.review_entries()
    first[0]["title"] = "tampered"
    first[0]["sources"][0]["url"] = "https://example.invalid"
    second = black_history_catalogue.review_entries()
    assert second[0]["title"] != "tampered"
    assert "example.invalid" not in second[0]["sources"][0]["url"]


def test_anonymous_user_cannot_view_founder_review(anonymous_client):
    response = anonymous_client.get("/library/black-history/review")
    assert response.status_code in (401, 403)
    assert b"bh-cape-uprising-1808" not in response.data
