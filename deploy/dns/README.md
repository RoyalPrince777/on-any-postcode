# OAP DNS — offline migration gate (inactive)

This is a **source-only** preparation for founder-controlled DNS migration. It provisions no DNS instances, performs no network checks, edits no IONOS records, and does not authorize nameserver delegation.

## Existing state and order

1. **Recover OAP World first** on an independently verified first-party application VPS, using existing `deploy/selfhost` Caddy/Compose source and real authentication/database secrets. Preserve current DNS until server identity, TLS, and health checks succeed.
2. Obtain a complete, current DNS zone inventory directly from IONOS, including A, AAAA, CNAME, MX, TXT/SPF, DKIM, DMARC, autodiscover, CAA, SRV and any non-web records. Do not use screenshots alone as a complete inventory.
3. Record the provenance and verification date privately; do **not** commit customer details, secrets or a live records export. Run `python scripts/oap_dns_inventory_check.py /path/to/verified-records.json` as a basic structure check. **Passing this script does not prove record equivalence or authorize deployment.**
4. Provision `ns1.onanypostcode.global` and `ns2.onanypostcode.global` on genuinely independent VPS infrastructure, running maintained authoritative DNS software. Do not mix authoritative DNS with a public recursive resolver. Secure zone transfer and administration, permit inbound UDP/TCP 53, and arrange monitored backups.
5. Replicate the complete verified zone. Verify matching authoritative answers for every required record from **both** servers through external networks and check SOA serials, negative responses, DNSSEC state, DNS delegation and email continuity.
6. Only after server IPs are known and documented, prepare registrar glue records for in-bailiwick `ns1`/`ns2`. Validate glue and parent delegation against child NS answers. If an existing registrar DS record exists, coordinate DNSSEC continuity first; **never create a broken DS chain**.
7. Request explicit Founder Final before changing registrar nameservers. Verify the public DNS, HTTPS, MX/mail and OAP World/Connect 4 after a supervised delegation change. Retain rollback records.

## Inventory input shape (illustrative placeholders, NOT production records)

```json
{
  "domain": "onanypostcode.global",
  "source": "verified IONOS DNS export",
  "source_verified_at": "YYYY-MM-DD",
  "delegation_approved": false,
  "records": [
    {"host": "@", "type": "A", "value": "REPLACE_WITH_VERIFIED_IPV4"},
    {"host": "@", "type": "AAAA", "value": "REPLACE_WITH_VERIFIED_IPV6"},
    {"host": "@", "type": "MX", "value": "REPLACE_WITH_VERIFIED_MAIL_TARGET"},
    {"host": "@", "type": "TXT", "value": "REPLACE_WITH_VERIFIED_SPF"},
    {"host": "_dmarc", "type": "CNAME", "value": "REPLACE_WITH_VERIFIED_TARGET"},
    {"host": "s1-ionos._domainkey", "type": "CNAME", "value": "REPLACE_WITH_VERIFIED_TARGET"},
    {"host": "autodiscover", "type": "CNAME", "value": "REPLACE_WITH_VERIFIED_TARGET"}
  ]
}
```

The placeholder inventory **must fail validation** until real IPv4 and IPv6 values are provided. A real zone may use different record names and include many additional entries. Never commit the real inventory to a public repository unless its disclosure has been explicitly reviewed.

**Green Gate:** no claim of DNS availability, ownership of physical servers, certificate issuance, successful deployment, or live Connect 4 is established by these files.
