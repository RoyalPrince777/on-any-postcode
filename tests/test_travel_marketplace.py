from mission_control import travel_marketplace


class _Stamp:
    def __init__(self, value):
        self.value = value

    def isoformat(self):
        return self.value


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return list(self.rows)


class _Connection:
    def __init__(self, rows):
        self.rows = rows
        self.query = None
        self.params = None

    def execute(self, query, params=()):
        self.query = query
        self.params = params
        return _Result(self.rows)


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def test_public_direct_discovery_exposes_only_privacy_reduced_offer(monkeypatch):
    monkeypatch.setattr(
        travel_marketplace.travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": True},
    )
    row = (
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
        "stay",
        "OAP Stay",
        "Direct Certified stay",
        "Mitcham",
        "CR4",
        "Merton",
        "United Kingdom",
        _Stamp("2026-09-10T14:00:00+00:00"),
        _Stamp("2026-09-11T10:00:00+00:00"),
        10,
        2,
        3,
        12500,
        "GBP",
        "per night",
        _Stamp("2026-09-04T12:00:00+00:00"),
        "Certified Stay Ltd",
    )
    connection = _Connection([row])
    monkeypatch.setattr(
        travel_marketplace.postgres_db,
        "connect",
        lambda readonly=False: _Context(connection),
    )

    current = travel_marketplace.public_offers(
        category="stay",
        country="United Kingdom",
        limit=10,
    )

    assert current["ready"] is True
    assert current["count"] == 1
    offer = current["offers"][0]
    assert offer["source"] == "oap_direct"
    assert offer["certified_supplier"] is True
    assert offer["available_quantity"] == 5
    assert offer["unit_price_minor"] == 12500
    assert offer["currency"] == "GBP"
    assert offer["observed_not_inferred"] is True
    assert offer["provider_authority"] is False
    assert "buyer_identity_id" not in offer
    assert "supplier_id" not in offer
    assert "p.state='CERTIFIED'" in connection.query
    assert "l.state='ACTIVE'" in connection.query
    assert "s.state='ACTIVE'" in connection.query


def test_public_direct_discovery_rejects_unknown_category(monkeypatch):
    monkeypatch.setattr(
        travel_marketplace.travel_supply_core,
        "supply_core_schema_status",
        lambda: {"schema_ready": True},
    )
    try:
        travel_marketplace.public_offers(category="not-a-real-category")
    except ValueError as exc:
        assert "invalid_supply_category" in str(exc)
    else:
        raise AssertionError("unknown categories must fail closed")


def test_founder_snapshot_preserves_constitutional_boundaries(monkeypatch):
    monkeypatch.setattr(
        travel_marketplace.travel_supply_core,
        "status",
        lambda: {"schema_ready": False},
    )
    current = travel_marketplace.founder_snapshot()

    assert current["creates_intelligence_worlds"] is False
    assert current["creates_agents"] is False
    assert current["creates_brain"] is False
    assert current["external_provider_authority"] is False
    assert current["guardian_gate_required"] is True
    assert current["human_authority_final"] is True
    assert current["suppliers"] == []
    assert current["listings"] == []
    assert current["inventory"] == []
    assert current["reservations"] == []
