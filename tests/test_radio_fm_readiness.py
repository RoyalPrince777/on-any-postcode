from uuid import uuid4

import pytest

from mission_control import radio_core


@pytest.mark.parametrize("injected", [
    {"broadcast_live": True, "public_stream_url": "https://example.test/live"},
    {"stream_url": "https://example.test/live", "stopped": False},
    {"broadcast_started": True, "state": "ACTIVE"},
])
def test_radio_metadata_cannot_claim_live_from_caller(injected):
    record = {"station_id": str(uuid4()), "name": "OAP Radio", "state": "ACTIVE", **injected}
    projected = radio_core.station_projection(record)
    assert projected is not None
    assert projected["broadcast_live"] is False
    assert projected["public_stream_url"] is None


@pytest.mark.parametrize("bad_stopped", [None, "", 0, [], {}, "false"])
def test_radio_stop_projection_must_not_infer_running_from_malformed_values(bad_stopped):
    record = {"station_id": str(uuid4()), "name": "OAP Radio", "state": "ACTIVE", "stopped": bad_stopped}
    projected = radio_core.station_projection(record)
    assert projected is None or projected["stopped"] is True
