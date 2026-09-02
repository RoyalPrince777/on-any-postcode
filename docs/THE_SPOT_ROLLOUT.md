# The Spot rollout order

1. Review branch diff for accidental removal or duplicate functionality.
2. Execute focused Spot tests in a real runtime.
3. Merge only after the tests and review are clean.
4. Deploy the merged main revision to the intended Render services.
5. Verify anonymous `/the-spot` behavior and private fail-closed behavior.
6. Verify a real postcode through the location/weather capability.
7. Verify mobile presentation.
8. Continue capability-by-capability proof gates; do not turn a rendered card into a transactional green status.
