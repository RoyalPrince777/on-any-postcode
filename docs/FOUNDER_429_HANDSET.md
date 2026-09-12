# Affected handset test

In Termux from the handset that experiences Too Many Requests:

```sh
git fetch origin fix/founder-429-diagnostics
git show origin/fix/founder-429-diagnostics:scripts/probe_founder_429.sh > /tmp/probe_founder_429.sh
sh /tmp/probe_founder_429.sh https://oap-smi.onrender.com
```

The probe is anonymous. Do not paste or type the Founder credential into it.
