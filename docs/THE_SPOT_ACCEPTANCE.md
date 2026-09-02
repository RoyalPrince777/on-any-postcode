# The Spot acceptance checklist

Before merge/deploy:

- Confirm branch remains based on the intended main revision.
- Run the Spot regression tests in a real Python test runtime; committed tests alone are not proof.
- Confirm `/the-spot` returns 200 and `Cache-Control: no-store`.
- Confirm the front door contains no form.
- Confirm all 19 canonical public capability names remain reachable.
- Confirm an HTML-like postcode query is escaped, not executed.
- Confirm anonymous browsing does not open My World or another private dashboard.
- Confirm the UI does not describe checkout, dispatch, payment, live tracking, or verification as live without runtime proof.

After deploy:

- Check the public Spot from an anonymous session.
- Check a real postcode through Maps, Weather & Travel.
- Check mobile layout and keyboard navigation.
- Record any failed capability as a blocker rather than masking it with a green label.
