"""Regression tests for private-by-default worldwide OAP Area matching policy."""
from copy import deepcopy

import pytest

from mission_control.activity_match_policy import eligible


def person(identity):
    return dict(identity_id=identity, adult_verified=True, matching_consent=True,
                discovery_enabled=True, interests=['Chess', 'Oware'],
                format='both', scope='worldwide', country='GB', area_id='mitcham')


def test_worldwide_compatible():
    assert eligible(person('one'), dict(person('two'), country='GH'))


@pytest.mark.parametrize('field,value', [
    ('adult_verified', None), ('adult_verified', False),
    ('matching_consent', False), ('matching_consent', None),
    ('discovery_enabled', False), ('interests', []), ('format', 'unknown'),
])
def test_fail_closed_for_either_member(field, value):
    for target in (0, 1):
        pair = [person('one'), person('two')]
        pair[target][field] = value
        assert not eligible(*pair)


def test_blocks_self_and_formats():
    assert not eligible(person('one'), person('two'), blocked=True)
    assert not eligible(person('one'), person('one'))
    assert not eligible(dict(person('one'), format='online'), dict(person('two'), format='in_person'))


def test_geographic_boundaries():
    assert not eligible(dict(person('one'), scope='country'), dict(person('two'), country='GH'))
    assert not eligible(dict(person('one'), scope='area'), dict(person('two'), area_id='begoro'))
    assert eligible(dict(person('one'), scope='country'), person('two'))


def test_does_not_mutate_personal_records():
    a, b = person('one'), person('two')
    before = deepcopy((a, b))
    eligible(a, b)
    assert (a, b) == before
