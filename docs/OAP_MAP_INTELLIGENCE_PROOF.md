# Map Intelligence proof checklist

Repository proof expected before merge:

- one public Map Intelligence capability
- canonical compatibility slug `maps-weather-travel`
- retired duplicate `movement-delivery`
- Map, Routes, Weather, Travel, Movement, OAP Direct, Booking and Delivery represented in the product contract
- no weakening of protected Movement backend boundaries
- no production deployment in this branch
- CI green on the final PR head

If main advances, reconcile the branch before merge and rerun CI. Do not call the release green from branch code alone.
