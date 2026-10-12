"""SMI advisory naming ballots: history, leader recovery and Founder Final boundary.

Pure read-only projection. No autonomous agent votes, persistence or execution grants.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class NamingRound:
    round_id: str
    candidates: tuple[str, ...]
    advisory_ballots: tuple[tuple[str, str], ...] = ()
    provenance: str = "illustrative_role_based"
    founder_approved: bool = False


@dataclass(frozen=True)
class NamingProjection:
    candidates: tuple[str, ...]
    recovered_leaders: tuple[str, ...]
    historical_wins: tuple[tuple[str, int], ...]
    current_votes: tuple[tuple[str, int], ...]
    missing_leaders: tuple[str, ...]
    advisory_only: bool = True
    founder_final_required: bool = True
    runtime_verified: bool = False


def _tally(round_: NamingRound) -> Counter[str]:
    if len({role for role, _ in round_.advisory_ballots}) != len(round_.advisory_ballots):
        raise ValueError("duplicate agent role in a single round")
    if any(candidate not in round_.candidates for _, candidate in round_.advisory_ballots):
        raise ValueError("ballot for unknown candidate")
    return Counter(candidate for _, candidate in round_.advisory_ballots)


def project_naming_vote(
    history: Sequence[NamingRound],
    proposed_candidates: Sequence[str],
    *,
    protected: Sequence[str] = ("KORADASO",),
) -> NamingProjection:
    """Carry historical winners into each new slate without pretending to run agents."""
    if not history:
        raise ValueError("historical round evidence required")
    if len({round_.round_id for round_ in history}) != len(history):
        raise ValueError("duplicate round identifiers")
    if any(round_.provenance != "illustrative_role_based" for round_ in history):
        raise ValueError("unsupported provenance: no authenticated agent ballots")
    wins: Counter[str] = Counter()
    leaders: list[str] = []
    for round_ in history:
        counts = _tally(round_)
        if counts:
            highest = max(counts.values())
            for candidate in round_.candidates:
                if counts[candidate] == highest:
                    wins[candidate] += 1
                    if candidate not in leaders:
                        leaders.append(candidate)
    for name in protected:
        if name not in leaders:
            leaders.append(name)
    current = tuple(dict.fromkeys(proposed_candidates))
    missing = tuple(name for name in leaders if name not in current)
    recovered = current + missing
    latest_counts = _tally(history[-1])
    return NamingProjection(
        candidates=recovered,
        recovered_leaders=missing,
        historical_wins=tuple(sorted(wins.items(), key=lambda item: (-item[1], item[0]))),
        current_votes=tuple(sorted(latest_counts.items(), key=lambda item: (-item[1], item[0]))),
        missing_leaders=missing,
    )


# Historic *illustrative* council outcomes only; not live autonomous ballots.
# Keep round identifiers stable even when earlier conversation labels varied.
HISTORICAL_NAMING_ROUNDS = (
    NamingRound("korakwan-council", ("KORAKWAN",), (("SMI", "KORAKWAN"),)),
    NamingRound("different-names", ("KORADASO",), (("SMI", "KORADASO"),)),
    NamingRound("oap-language", ("KORADASO",), (("SMI", "KORADASO"),)),
    NamingRound("south-london", ("ALL ENDZ",), (("SMI", "ALL ENDZ"),)),
    NamingRound("round-5", ("KORADASO",), (("SMI", "KORADASO"),)),
)

# Newly proposed South London x Ghana x OAP Language challenger slate.
NEW_CHALLENGERS = (
    "YARDLINK", "ENDZWAY", "SOUTH ROOTS", "NANA CONNECT",
    "WORLD YARD", "AKYEM ROAD", "POSTCODE PALACE",
)
