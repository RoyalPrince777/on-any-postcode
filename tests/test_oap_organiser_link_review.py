from pathlib import Path


def test_oap_organiser_exposes_the_link_weekly_review_preset():
    page = Path("templates/oap_lab.html").read_text(encoding="utf-8")

    assert 'id="organiser-weekly-link-review"' in page
    assert "The Link · Weekly Review" in page
    assert "Link Call stays canonical" in page
    assert "🟣 Continue" in page
    assert "Add to OAP Organiser" in page
    assert "the-link-weekly-review" in page
    assert "RRULE:FREQ=WEEKLY;BYDAY=WE" in page
    assert "/api/smi-organiser/schedules/" in page
    assert "Not written until Founder action." in page
    assert "Google Calendar" not in page
