from __future__ import annotations

import pytest

from oap.contracts import BrainRequest
from oap.nexus.router import NexusRouter, SignalValidationError
from oap.smi.organs.thalamus import Thalamus


def test_oapdata_is_the_canonical_signal_context():
    request = BrainRequest(
        request_id="req-oapdata-1",
        identity_id="human-1",
        content="Check the postcode context",
        task_type="COMMUNITY",
        oapdata={"postcode": "CR4", "culture": "Akan"},
    )

    assert request.oapdata == {"postcode": "CR4", "culture": "Akan"}
    assert request.metadata == request.oapdata

    envelope = NexusRouter().receive(request)
    signal = Thalamus().receive(envelope)

    assert signal.oapdata == request.oapdata
    assert signal.metadata == signal.oapdata
    assert NexusRouter().status()["data_language"] == "OAPDATA"


def test_thalamus_redacts_private_values_inside_oapdata():
    request = BrainRequest(
        request_id="req-oapdata-2",
        identity_id="human-1",
        content="Review this bounded context",
        oapdata={
            "postcode": "CR4",
            "token": "do-not-propagate",
            "nested": {"private_key": "do-not-propagate"},
        },
    )

    signal = Thalamus().receive(NexusRouter().receive(request))

    assert signal.oapdata["postcode"] == "CR4"
    assert signal.oapdata["token"] == "<REDACTED>"
    assert signal.oapdata["nested"]["private_key"] == "<REDACTED>"


def test_nexus_rejects_non_object_oapdata():
    request = BrainRequest(
        request_id="req-oapdata-3",
        identity_id="human-1",
        content="Review",
        oapdata=["not", "an", "object"],  # type: ignore[arg-type]
    )

    with pytest.raises(SignalValidationError, match="Signal OAPDATA must be an object"):
        NexusRouter().receive(request)


def test_legacy_metadata_input_maps_into_oapdata_without_becoming_canonical():
    request = BrainRequest(
        request_id="req-oapdata-legacy",
        identity_id="human-1",
        content="Compatibility check",
        metadata={"location": "Mitcham"},
    )

    assert request.oapdata == {"location": "Mitcham"}

    with pytest.raises(TypeError, match="Use oapdata only"):
        BrainRequest(
            request_id="req-oapdata-conflict",
            identity_id="human-1",
            content="Conflict",
            oapdata={"postcode": "CR4"},
            metadata={"postcode": "SW11"},
        )
