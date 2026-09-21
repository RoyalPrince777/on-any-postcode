# SMI Android motion evidence gate v0.1

This offline gate evaluates a receipt from a real, Human-observed Android run.
It cannot manufacture evidence, approve production, publish assets or connect
the isolated motion candidate to the live SMI page.

Acceptance requires the exact approved source, all seven layer hashes, an
Android device identity, fresh test time, played-audio clock delta no greater
than 80 ms, STOP acknowledgement no greater than 50 ms, confirmed audio and
motion cessation, background STOP, exact-character visual integrity and
explicit Human visual approval.

An accepted receipt advances only the 75% Aegis evidence decision. The result
always keeps `productionApproved` and `humanFinalApproved` false. The separate
100% Green Gate and Founder Final remain mandatory.
