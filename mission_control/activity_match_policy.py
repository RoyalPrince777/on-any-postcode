"""Private, pure-policy OAP Area activities matching eligibility.

Not a runtime directory, persistent store, route, or release authorisation.
"""
from __future__ import annotations

from collections.abc import Mapping

ALLOWED_FORMATS = frozenset({'online', 'in_person', 'both'})


def eligible(viewer: Mapping[str, object], candidate: Mapping[str, object], *, blocked: bool = False) -> bool:
    """Fail closed on missing proof, withdrawal, blocks or incompatible scope."""
    if blocked or not isinstance(viewer, Mapping) or not isinstance(candidate, Mapping):
        return False
    if not viewer.get('identity_id') or not candidate.get('identity_id'):
        return False
    if viewer['identity_id'] == candidate['identity_id']:
        return False
    for person in (viewer, candidate):
        if person.get('adult_verified') is not True:
            return False
        if person.get('matching_consent') is not True:
            return False
        if person.get('discovery_enabled') is not True:
            return False
    left = viewer.get('interests')
    right = candidate.get('interests')
    if not isinstance(left, (tuple, list, set, frozenset)) or not isinstance(right, (tuple, list, set, frozenset)):
        return False
    if not ({x.strip().casefold() for x in left if isinstance(x, str) and x.strip()} &
            {x.strip().casefold() for x in right if isinstance(x, str) and x.strip()}):
        return False
    a, b = viewer.get('format'), candidate.get('format')
    if a not in ALLOWED_FORMATS or b not in ALLOWED_FORMATS:
        return False
    if a != 'both' and b != 'both' and a != b:
        return False
    if viewer.get('scope') not in ('worldwide', 'country', 'area'):
        return False
    if viewer['scope'] == 'country' and (not viewer.get('country') or viewer.get('country') != candidate.get('country')):
        return False
    if viewer['scope'] == 'area' and (not viewer.get('area_id') or viewer.get('area_id') != candidate.get('area_id')):
        return False
    return True
