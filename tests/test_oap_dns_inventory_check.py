"""Offline DNS inventory gate: no DNS writes or network calls."""
from scripts.oap_dns_inventory_check import validate, compare_with_verified_baseline


def sample():
    return {
        "domain": "onanypostcode.global",
        "source": "verified IONOS export",
        "source_verified_at": "2026-11-01",
        "delegation_approved": False,
        "records": [
            {"host": "@", "type": "A", "value": "192.0.2.10"},
            {"host": "@", "type": "AAAA", "value": "2001:db8::10"},
            {"host": "@", "type": "MX", "value": "mail.example.invalid"},
            {"host": "@", "type": "TXT", "value": "v=spf1 -all"},
            {"host": "_dmarc", "type": "TXT", "value": "v=DMARC1; p=reject"},
            {"host": "s1._domainkey", "type": "TXT", "value": "v=DKIM1; p=example"},
            {"host": "autodiscover", "type": "CNAME", "value": "mail.example.invalid"},
        ],
    }


def test_structural_inventory_not_delegation_approval():
    assert validate(sample()) == []


def test_missing_source_fails_closed():
    inventory = sample()
    inventory.pop("source_verified_at")
    assert validate(inventory)


def test_incorrect_address_family_fails_closed():
    inventory = sample()
    inventory["records"][0]["value"] = "2001:db8::10"
    assert any("address family mismatch" in error for error in validate(inventory))


def test_cannot_authorize_delegation():
    inventory = sample()
    inventory["delegation_approved"] = True
    assert any("cannot authorize delegation" in error for error in validate(inventory))


def test_missing_email_records_fails_closed():
    inventory = sample()
    inventory["records"] = inventory["records"][:2]
    assert any("missing MX" in error for error in validate(inventory))


def test_baseline_exact_equivalence():
    assert compare_with_verified_baseline(sample(), sample()) == []


def test_baseline_rejects_missing_individual_record():
    candidate = sample()
    candidate["records"] = candidate["records"][:-1]
    assert any("differ from verified baseline" in e for e in compare_with_verified_baseline(candidate, sample()))


def test_baseline_rejects_modified_mail_target():
    candidate = sample()
    candidate["records"][2]["value"] = "different.example.invalid"
    assert any("differ from verified baseline" in e for e in compare_with_verified_baseline(candidate, sample()))


def test_baseline_rejects_unexpected_record():
    candidate = sample()
    candidate["records"].append({"host": "unexpected", "type": "TXT", "value": "extra"})
    assert any("differ from verified baseline" in e for e in compare_with_verified_baseline(candidate, sample()))
