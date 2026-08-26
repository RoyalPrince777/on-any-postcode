from __future__ import annotations

import pytest

from oap.contracts import BrainRequest
from oap.nexus.router import NexusRouter, SignalValidationError
from oap.smi.organs.thalamus import Thalamus


def test_oapcore_is_the_canonical_signal_context():
    request = BrainRequest(
        request_id="req-oapcore-1",
        identity_id="human-1",
        content="Check the postcode context",
        task_type="COMMUNITY",
        oapcore={"postcode": "CR4", "culture": "Akan"},
    )

    assert request.oapcore == {"postcode": "CR4", "culture": "Akan"}
    assert request.oapdata == request.oapcore
    assert request.metadata == request.oapcore

    envelope = NexusRouter().receive(request)
    signal = Thalamus().receive(envelope)

    assert signal.oapcore == request.oapcore
    assert signal.oapdata == signal.oapcore
    assert signal.metadata == signal.oapcore
    assert NexusRouter().status()["context_language"] == "OAP CORE"


def test_thalamus_redacts_private_values_inside_oapcore():
    request = BrainRequest(
        request_id="req-oapcore-2",
        identity_id="human-1",
        content="Review this bounded context",
        oapcore={
            "postcode": "CR4",
            "token": "do-not-propagate",
            "nested": {"private_key": "do-not-propagate"},
        },
    )

    signal = Thalamus().receive(NexusRouter().receive(request))

    assert signal.oapcore["postcode"] == "CR4"
    assert signal.oapcore["token"] == "<REDACTED>"
    assert signal.oapcore["nested"]["private_key"] == "<REDACTED>"


def test_nexus_rejects_non_object_oapcore():
    request = BrainRequest(
        request_id="req-oapcore-3",
        identity_id="human-1",
        content="Review",
        oapcore=["not", "an", "object"],  # type: ignore[arg-type]
    )

    with pytest.raises(SignalValidationError, match="Signal OAP CORE must be an object"):
        NexusRouter().receive(request)


def test_legacy_names_map_into_oapcore_without_becoming_canonical():
    from_oapdata = BrainRequest(
        request_id="req-oapcore-oapdata-legacy",
        identity_id="human-1",
        content="Compatibility check",
        oapdata={"location": "Mitcham"},
    )
    from_metadata = BrainRequest(
        request_id="req-oapcore-metadata-legacy",
        identity_id="human-1",
        content="Compatibility check",
        metadata={"location": "Mitcham"},
    )

    assert from_oapdata.oapcore == {"location": "Mitcham"}
    assert from_metadata.oapcore == {"location": "Mitcham"}

    with pytest.raises(TypeError, match="Use oapcore only"):
        BrainRequest(
            request_id="req-oapcore-conflict",
            identity_id="human-1",
            content="Conflict",
            oapcore={"postcode": "CR4"},
            oapdata={"postcode": "SW11"},
        )
