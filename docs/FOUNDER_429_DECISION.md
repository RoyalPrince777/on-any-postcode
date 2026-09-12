# Founder 429 decision table

| Existing route | Alternate route | Interpretation |
|---|---|---|
| 429 | 200 | likely path-specific upstream rule |
| 429 | 429 | likely broader upstream limiter; alternate path is not the fix |
| app page | app page | edge is passing both; inspect later request that returns 429 |
| other | other | capture headers and trace the responding layer before mutation |
