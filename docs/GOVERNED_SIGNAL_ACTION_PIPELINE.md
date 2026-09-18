# Governed Signal Action Pipeline

Status: draft integration gate. No production deployment is implied.

Canonical runtime path:

`Signal → agents → Judgement → Guardian → Human Authority → bounded Action adapter → HRM receipt`

The implementation composes existing OAP systems rather than creating another intelligence brain. Matrix Signal Bus supplies the auditable Signal envelope, the canonical live brain selects and runs approved advisers plus Guardian/War Room review, Judgement produces the explainable review record, Human Authority remains final for consequential/external action, and HRM uses the existing canonical 7-7-7 receipt contract.

Hard boundaries:

- no authority transfer through Signal or agent handoff;
- no self-approval;
- no external action without Guardian pass and required Human Authority approval;
- no action without an explicit execution adapter;
- no durable HRM write without an explicit receipt writer;
- production durable writes remain governed by the existing opt-in HRM write gate;
- a review-only Signal can never execute an external action;
- Guardian can block an action even when Human Authority approval is present;
- every built receipt uses the canonical Mind 7 / Body 7 / Soul 7 check names.

This bridge does not widen Founder access, change permissions, deploy, publish, dispatch, move money or enable autonomous execution by itself.