from mission_control.esim_provisioning import EsimProvisioningCore


class FakeProvider:
    name = "fake-provider"

    def provision(self, *, request_id: str, subject_id: str) -> dict:
        return {"provider_profile_id": f"profile-{request_id}", "active": True}

    def suspend(self, *, provider_profile_id: str) -> dict:
        return {"suspended": True}

    def resume(self, *, provider_profile_id: str) -> dict:
        return {"active": True}

    def revoke(self, *, provider_profile_id: str) -> dict:
        return {"revoked": True}


def test_provider_required_before_provisioning():
    core = EsimProvisioningCore()
    item = core.request(subject_id="founder", purpose="connectivity")
    core.approve(item["request_id"], founder_identity="founder")

    try:
        core.provision(item["request_id"])
    except RuntimeError as exc:
        assert str(exc) == "esim_provider_not_configured"
    else:
        raise AssertionError("provisioning must fail closed without a provider")


def test_approval_required_before_provisioning():
    core = EsimProvisioningCore(FakeProvider())
    item = core.request(subject_id="founder", purpose="connectivity")

    try:
        core.provision(item["request_id"])
    except PermissionError as exc:
        assert str(exc) == "approved_request_required"
    else:
        raise AssertionError("provisioning must require explicit approval")


def test_full_lifecycle_requires_provider_confirmation():
    core = EsimProvisioningCore(FakeProvider())
    item = core.request(subject_id="founder", purpose="connectivity")
    request_id = item["request_id"]

    approved = core.approve(request_id, founder_identity="founder")
    assert approved["state"] == "approved"

    active = core.provision(request_id)
    assert active["state"] == "active"
    assert active["provider_profile_id"]

    suspended = core.suspend(request_id)
    assert suspended["state"] == "suspended"

    resumed = core.resume(request_id)
    assert resumed["state"] == "active"

    revoked = core.revoke(request_id)
    assert revoked["state"] == "revoked"

    events = [event["event"] for event in core.events(request_id)]
    assert events == [
        "requested",
        "approved",
        "provisioning",
        "active",
        "suspended",
        "active",
        "revoked",
    ]
