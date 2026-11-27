"""Property routing stays within the canonical SMI and its provider boundary."""
from oap.contracts import FocusedSignal
from oap.smi.agi_core import AGICore
from oap.smi.providers import ProviderRouter


def property_signal():
    return FocusedSignal(
        request_id="property-test",
        identity_id="test-identity",
        task_type="PROPERTY",
        content="Private property recommendation",
        oapcore={},
        high_impact=True,
        tags=(),
    )


def test_property_routes_through_seven_existing_worlds():
    route = AGICore().route("Private opportunity", "PROPERTY")
    assert set(route["world_ids"]) == {
        "earth", "language", "life", "movement", "civic", "civilisation", "matrix",
    }
    assert "distribution" in route["specialist_ids"]
    assert route["world_count_limit"] == 7
    assert not route["execution_authority"]
    assert not route["decision_authority"]
    assert route["human_authority_final"]


def test_property_requires_no_assigned_provider():
    assert ProviderRouter().route(property_signal()) == ()


def test_property_denies_external_provider_even_if_assigned():
    class External:
        provider_id = "external-test"
        sovereign_scope = "external"
        called = False

        def analyse(self, signal):
            self.called = True
            raise AssertionError("External property data egress")

    adapter = External()
    router = ProviderRouter(
        adapters=(adapter,),
        approved_assignments={"PROPERTY": adapter.provider_id},
    )
    result, = router.route(property_signal())
    assert not result.available
    assert result.error_code == "property_external_provider_blocked"
    assert not adapter.called
