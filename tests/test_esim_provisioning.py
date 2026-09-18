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


class FakeRepository:
    def __init__(self) -> None:
        self.requests: dict[str, dict] = {}
        self.event_rows: list[dict] = []

    def save_request(self, item: dict) -> None:
        self.requests[item["request_id"]] = dict(item)

    def append_event(self, event: dict) -> None:
        self.event_rows.append(dict(event))

    def save_with_event(self, item: dict, event: dict) -> None:
        self.requests[item["request_id"]] = dict(item)
        self.event_rows.append(dict(event))

    def get_request(self, request_id: str) -> dict | None:
        item = self.requests.get(request_id)
        return dict(item) if item is not None else None

    def list_events(self, request_id: str) -> list[dict]:
        return [
            dict(event)
            for event in self.event_rows
            if event["request_id"] == request_id
        ]


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


def test_repository_restores_state_across_core_restart():
    repository = FakeRepository()
    first = EsimProvisioningCore(repository=repository)
    item = first.request(subject_id="founder", purpose="connectivity")
    request_id = item["request_id"]
    first.approve(request_id, founder_identity="founder")

    second = EsimProvisioningCore(repository=repository)
    restored = second.get(request_id)

    assert restored["state"] == "approved"
    assert restored["approved_by"] == "founder"
    assert [event["event"] for event in second.events(request_id)] == [
        "requested",
        "approved",
    ]
