# Founder 429 proof requirement

Do not mark the incident green merely because code or CI passes.

Green requires affected-path evidence showing that the Founder entry page can be reached without HTTP 429 while the Founder-only security boundary remains intact. If the rejection is upstream, the final repair belongs at that upstream boundary rather than in the Flask credential handler.
