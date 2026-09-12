# Diagnostic noise policy

The probe intentionally avoids response bodies, cookies, credentials, and verbose curl traces. Only boundary-relevant response metadata is printed so the incident can be diagnosed without leaking Founder information.
