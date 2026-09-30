"""Best of the Decade nomination eligibility, without a second Awards system.

This pure guard can be called by the existing OAP Awards admission path once
the Founder has approved the decade boundaries. It performs no publishing,
voting, award, approval or payment action.
"""

from datetime import date


def check_decade_nomination(record, *, first_year, last_year):
    """Return (eligible, reason); fail closed for missing/uncorroborated dates.

    record keys: nominee_name, award_type, achievement_date (ISO YYYY-MM-DD),
    evidence_reference. Historical awards rows have no achievement_date or
    evidence_reference and must not be silently admitted.
    """
    if not isinstance(first_year, int) or isinstance(first_year, bool):
        raise TypeError("first_year must be an integer")
    if not isinstance(last_year, int) or isinstance(last_year, bool):
        raise TypeError("last_year must be an integer")
    if first_year < 1 or last_year > 9999 or last_year - first_year != 9:
        raise ValueError("explicit inclusive ten-calendar-year boundaries required")
    if not isinstance(record, dict):
        return False, "invalid_record"
    if not str(record.get("nominee_name") or "").strip():
        return False, "missing_nominee"
    if not str(record.get("award_type") or "").strip():
        return False, "missing_category"
    if not str(record.get("evidence_reference") or "").strip():
        return False, "missing_evidence"
    raw = record.get("achievement_date")
    if not isinstance(raw, str) or len(raw) != 10:
        return False, "missing_or_invalid_achievement_date"
    try:
        achieved = date.fromisoformat(raw)
    except ValueError:
        return False, "missing_or_invalid_achievement_date"
    if achieved.isoformat() != raw:
        return False, "missing_or_invalid_achievement_date"
    if not first_year <= achieved.year <= last_year:
        return False, "outside_decade"
    return True, "eligible_for_review"
