# OAP Founder Tool Approval Boundary

Founder tool proposals are exact ActionPlans. Human Authority approval signs the proposal action digest and records the receipt in the existing approval/audit store. Approval never executes the tool. The next gate remains Living Kernel, which must verify the receipt and exact plan before Builder can invoke a registered mutation adapter.

Current approved Founder GitHub actions: branch creation on `oap-mind/*`, file write on `oap-mind/*`, and pull-request creation targeting `main`. Direct `main` writes, pull-request merge, Render deploy and database mutation remain outside this slice.
