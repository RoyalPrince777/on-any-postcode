"""Bounded real-data evidence verification for ON ANY POSTCODE Intelligence.

This organ observes and verifies evidence only. It never approves or executes actions.
Judgement, Aegis, Living Kernel and Human Authority remain separate authority layers.
"""
from __future__ import annotations

import hashlib
import ssl
import time
from dataclasses import dataclass, asdict
from urllib import request as urlrequest
from urllib.parse import urlparse


@dataclass(frozen=True)
class EvidenceReport:
    source_id: str
    source_url: str
    observed: bool
    verified: bool
    authoritative: bool
    observed_at: float
    age_seconds: float | None
    content_sha256: str | None
    status_code: int | None
    reason: str

    def public(self) -> dict[str, object]:
        return asdict(self)


OFFICIAL_SOURCE_DOMAINS = {
    "fifa.com",
    "www.fifa.com",
    "uefa.com",
    "www.uefa.com",
    "olympics.com",
    "www.olympics.com",
    "worldathletics.org",
    "www.worldathletics.org",
    "formula1.com",
    "www.formula1.com",
    "nba.com",
    "www.nba.com",
    "nfl.com",
    "www.nfl.com",
    "mlb.com",
    "www.mlb.com",
    "atptour.com",
    "www.atptour.com",
    "wtatennis.com",
    "www.wtatennis.com",
}


def _allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in OFFICIAL_SOURCE_DOMAINS


def verify_https_source(source_id: str, source_url: str, *, timeout_seconds: float = 4.0) -> EvidenceReport:
    now = time.time()
    if not _allowed(source_url):
        return EvidenceReport(source_id, source_url, False, False, False, now, None, None, None, "source_not_allowlisted")

    req = urlrequest.Request(source_url, headers={"User-Agent": "ON-ANY-POSTCODE-Evidence/1.0"})
    try:
        with urlrequest.urlopen(req, timeout=timeout_seconds, context=ssl.create_default_context()) as response:
            body = response.read(512_000)
            status = int(getattr(response, "status", 200))
    except Exception:
        return EvidenceReport(source_id, source_url, False, False, True, now, None, None, None, "source_unreachable")

    digest = hashlib.sha256(body).hexdigest()
    useful = status == 200 and len(body) >= 128
    return EvidenceReport(
        source_id=source_id,
        source_url=source_url,
        observed=True,
        verified=useful,
        authoritative=True,
        observed_at=now,
        age_seconds=0.0,
        content_sha256=digest,
        status_code=status,
        reason="official_source_observed" if useful else "insufficient_response",
    )


def coherent_evidence_status(reports: list[EvidenceReport]) -> dict[str, object]:
    observed = [item for item in reports if item.observed]
    verified = [item for item in reports if item.verified]
    authoritative = [item for item in verified if item.authoritative]
    return {
        "adaptive": True,
        "coherent": bool(verified) and len(verified) == len(observed),
        "observed_sources": len(observed),
        "verified_sources": len(verified),
        "authoritative_sources": len(authoritative),
        "can_execute": False,
        "human_authority_final": True,
        "reports": [item.public() for item in reports],
    }
