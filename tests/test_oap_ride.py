from uuid import uuid4
import pytest
from mission_control import oap_ride

def test_ride_status_has_12_core_functions_and_excludes_physical():
    state=oap_ride.status()
    assert len(state["flow"]) == 12
    assert state["physical_operations_in_scope"] is False
    assert state["guardian_transport"] is True
    assert state["incoming"] is True

def test_rider_driver_match_is_digital_only():
    req=oap_ride.create_request(rider_id=uuid4(), pickup="Mitcham", destination="Battersea")
    drv=oap_ride.driver_availability(driver_id=uuid4(), active=True, area="South London", vehicle_class="standard")
    match=oap_ride.propose_match(request=req, driver=drv)
    assert match["state"] == "MATCH_PROPOSED"
    assert match["incoming_journey"] is True
    assert match["dispatch_performed"] is False

def test_journey_code_required_before_pickup_verified():
    journey={"journey_id":str(uuid4()),"state":"ACCEPTED"}
    with pytest.raises(ValueError, match="journey_code_required"):
        oap_ride.transition(journey=journey,to_state="PICKUP_VERIFIED")
    result=oap_ride.transition(journey=journey,to_state="PICKUP_VERIFIED",journey_code_verified=True)
    assert result["journey_code_verified"] is True
    assert result["physical_dispatch_performed"] is False
