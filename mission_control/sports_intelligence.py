"""Sports Intelligence status backed by official-source verification.

This layer verifies real sports data availability. It does not treat cached fixtures,
hard-coded examples, or stale pages as live data.
"""
from __future__ import annotations

from .evidence_intelligence import coherent_evidence_status, verify_https_source

FIFA_WORLD_CUP_2026_URL = (
    "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/"
    "articles/match-schedule-fixtures-results-teams-stadiums"
)

SPORTS = (
    {"id":"football","name":"Football","status":"verification_connected","source":"FIFA official","url":FIFA_WORLD_CUP_2026_URL},
    {"id":"athletics","name":"Athletics","status":"registry_ready","source":"World Athletics official","url":"https://worldathletics.org/"},
    {"id":"motorsport","name":"Motorsport","status":"registry_ready","source":"Formula 1 official","url":"https://www.formula1.com/"},
    {"id":"basketball","name":"Basketball","status":"registry_ready","source":"NBA official","url":"https://www.nba.com/"},
    {"id":"american-football","name":"American Football","status":"registry_ready","source":"NFL official","url":"https://www.nfl.com/"},
    {"id":"baseball","name":"Baseball","status":"registry_ready","source":"MLB official","url":"https://www.mlb.com/"},
    {"id":"tennis-men","name":"Tennis (ATP)","status":"registry_ready","source":"ATP official","url":"https://www.atptour.com/"},
    {"id":"tennis-women","name":"Tennis (WTA)","status":"registry_ready","source":"WTA official","url":"https://www.wtatennis.com/"},
)


def status(*, probe: bool = False) -> dict[str, object]:
    reports = []
    sports = []
    for item in SPORTS:
        entry = dict(item)
        if probe:
            report = verify_https_source(str(item["id"]), str(item["url"]))
            reports.append(report)
            entry["observed"] = report.observed
            entry["verified"] = report.verified
        else:
            entry["observed"] = False
            entry["verified"] = False
        sports.append(entry)

    evidence = coherent_evidence_status(reports) if probe else {
        "adaptive": True,
        "coherent": False,
        "observed_sources": 0,
        "verified_sources": 0,
        "authoritative_sources": 0,
        "can_execute": False,
        "human_authority_final": True,
        "reports": [],
    }
    return {
        "name": "OAP Sports Intelligence",
        "mode": "official-source verification",
        "live_claim_allowed": bool(probe and evidence["verified_sources"]),
        "sports": sports,
        "evidence": evidence,
        "autonomy": {
            "observe": True,
            "verify": True,
            "compare": True,
            "adapt_read_models": True,
            "publish_unverified_as_live": False,
            "spend": False,
            "dispatch": False,
            "approve": False,
        },
    }
