# Relation to PR #217

PR #217 remains a candidate alternate path, not proof of a production fix. Its `/auth/founder-entry` route points at the same application Founder handler as `/auth/recover-founder`. Therefore it can only bypass an upstream rule that distinguishes paths.
