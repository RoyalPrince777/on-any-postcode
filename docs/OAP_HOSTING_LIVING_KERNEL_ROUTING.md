# OAP Hosting — Living Kernel routing contract (candidate)

Status: design contract only. No cloud deployment, live heartbeat, independent routing endpoint, or automatic recovery has been proven.

## Authority and ownership
Founder Final retains authority. SMI evaluates evidence; Captain ALL IN coordinates bounded execution. The existing Living Kernel (where implemented) owns observation and continuity evidence; it must not be replaced with a second supervisor. Fox selects viable infrastructure; Dozer executes approved recovery; Tank and Bagheera enforce security/privacy boundaries; the Twins compare expected and actual state; Shere Khan challenges unsupported Green claims.

## Existing routing deployment
- Portable runtime: `compose.routing.yml`, building the repository root `Dockerfile` (OSRM v6 / Greater London graph).
- Container port: 10000; Compose publishes it only to host loopback.
- HTTPS must be terminated by a separately configured and verified reverse proxy. Never configure the CI routing origin to an unverified host.
- The live Green Gate remains mandatory: `scripts/routing_live_green_gate.py` reads `OAP_ROUTING_GREEN_GATE_BASE_URL` from GitHub Actions repository variables.

## Living Kernel observations — evidence required
| Vital | Required evidence |
| --- | --- |
| Pulse | Real OSRM route probe result and timestamp |
| Awareness | Service state, endpoint identity and graph region/version |
| Circulation | Proxy-to-OSRM request success and latency |
| Integrity | Image digest, graph provenance, config fingerprint |
| Continuity | Durable prior-state and incident receipts |
| Energy | Host memory, CPU, disk capacity and saturation |
| Balance | Resource limits and concurrent request impact |
| Adaptation | Recorded recovery action and post-recovery proof |
| Participation | Named specialist review and authority boundaries |
| Purpose | Explicit OAP routing mission and supported region |

## State machine
- **UNVERIFIED**: no trustworthy runtime evidence.
- **BLOCKED**: required service or public HTTPS endpoint unavailable.
- **DEGRADED**: available but required latency, correctness, or resilience evidence fails.
- **RECOVERING**: approved remediation in progress; never equal to healthy.
- **HEALTHY**: current live route checks and mandatory external Green Gate pass on the exact deployment.

No inferred success from a container restart, image build, Compose syntax check, HTTP 200 without valid route geometry, or a passing unit-test suite.

## Next executable proof
1. Obtain authorised Docker-capable Linux runtime with adequate measured resources (outside billing-suspended Render workspace).
2. Build `docker compose -f compose.routing.yml build`; record image digest and graph-build resource consumption.
3. Run `docker compose -f compose.routing.yml up -d`; verify valid Greater London route geometry on loopback.
4. Establish HTTPS proxy with valid certificate, and confirm routing path end-to-end.
5. Set `OAP_ROUTING_GREEN_GATE_BASE_URL` to the verified HTTPS origin and run exact-head CI; collect Living Kernel receipts only from actual observations.

## Non-goals
No payment authorisation, cloud account creation, unsupported Android Docker claim, simulated uptime, automatic public failover, or claims of operational Living Kernel integration from this document alone.
