"""OAP Fashion versioned snapshot and fail-closed recovery tests."""
from copy import deepcopy

import pytest

from mission_control.fashion_first_party import (
    FashionDraft,
    FashionError,
    FashionState,
    FashionVariant,
)
from mission_control.fashion_snapshot import restore, snapshot

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
PRODUCT = "33333333-3333-4333-8333-333333333333"
OTHER_PRODUCT = "44444444-4444-4444-8444-444444444444"


def draft():
    return FashionDraft(
        OWNER, PRODUCT, "OAP Hoodie", "hoodie", "oap:art/001",
        True, True, (FashionVariant("OAP-HOODIE-001", "XL", "Black", 3500),),
    )


@pytest.mark.parametrize("phase", ["draft", "review", "approved", "stopped"])
def test_first_party_snapshot_round_trip_with_state_and_history(phase):
    original = draft()
    if phase in ("review", "approved", "stopped"):
        original.submit_review(OWNER, "rights:001")
    if phase in ("approved", "stopped"):
        original.approve(OWNER, "human:001", human_approval=True)
    if phase == "stopped":
        original.stop(OWNER, "STOP:001")
    envelope = snapshot(original, actor_id=OWNER)
    restored = restore(envelope, actor_id=OWNER, product_id=PRODUCT)
    assert restored.state == original.state
    assert restored.events == original.events
    assert restored.variants == original.variants
    assert envelope["durable_write_performed"] is False
    assert envelope["external_execution_performed"] is False


def test_snapshot_owner_and_product_fail_closed():
    envelope = snapshot(draft(), actor_id=OWNER)
    with pytest.raises(FashionError, match="not_product_owner"):
        snapshot(draft(), actor_id=OTHER)
    with pytest.raises(FashionError, match="not_product_owner"):
        restore(envelope, actor_id=OTHER, product_id=PRODUCT)
    with pytest.raises(FashionError, match="fashion_product_mismatch"):
        restore(envelope, actor_id=OWNER, product_id=OTHER_PRODUCT)


def test_snapshot_tampering_rejected_before_restore():
    envelope = snapshot(draft(), actor_id=OWNER)
    modified = deepcopy(envelope)
    modified["payload"]["state"] = FashionState.APPROVED.value
    with pytest.raises(FashionError, match="fashion_snapshot_digest_mismatch"):
        restore(modified, actor_id=OWNER, product_id=PRODUCT)


def test_unsupported_snapshot_version_fails_closed():
    envelope = snapshot(draft(), actor_id=OWNER)
    from mission_control import fashion_snapshot

    modified = deepcopy(envelope)
    modified["payload"]["version"] = 99
    modified["sha256"] = fashion_snapshot.hashlib.sha256(
        fashion_snapshot._canonical(modified["payload"])
    ).hexdigest()
    with pytest.raises(FashionError, match="unsupported_fashion_snapshot_version"):
        restore(modified, actor_id=OWNER, product_id=PRODUCT)


def test_invalid_state_history_fails_even_with_valid_digest():
    envelope = snapshot(draft(), actor_id=OWNER)
    from mission_control import fashion_snapshot

    modified = deepcopy(envelope)
    modified["payload"]["state"] = "APPROVED"
    modified["sha256"] = fashion_snapshot.hashlib.sha256(
        fashion_snapshot._canonical(modified["payload"])
    ).hexdigest()
    with pytest.raises(FashionError, match="invalid_fashion_events"):
        restore(modified, actor_id=OWNER, product_id=PRODUCT)


def test_stop_after_restore_blocks_market_projection():
    p = draft()
    p.submit_review(OWNER, "rights")
    p.approve(OWNER, "human", human_approval=True)
    p.stop(OWNER, "STOP")
    recovered = restore(snapshot(p, actor_id=OWNER), actor_id=OWNER, product_id=PRODUCT)
    with pytest.raises(FashionError, match="product_not_approved"):
        recovered.market_projection(OWNER)
