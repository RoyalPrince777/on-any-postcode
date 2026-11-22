"""Bank navigation reaches real pages without claiming financial execution."""
from html.parser import HTMLParser
from urllib.parse import urlsplit

import app as app_module
from mission_control import oap_pay


class _Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.menu_links = []
        self.in_menu = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "nav" and "data-bank-menu" in attrs:
            self.in_menu = True
        if self.in_menu and tag == "a":
            self.menu_links.append((attrs["href"], "data-private-account" in attrs))

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_menu = False


def test_bank_menu_has_six_sections_and_all_links_reach_existing_pages(client, monkeypatch):
    monkeypatch.setattr(oap_pay.sika_customer_view, "activity", lambda owner: {"items": []})
    page = _Page(client.get("/pay/bank").get_data(as_text=True))
    assert {"menu-my-sika", "menu-money-payments", "menu-cards-banking", "menu-global-sika",
            "menu-oap-ecosystem", "menu-security-support"} <= page.ids
    assert len(page.menu_links) == 21
    for href, _private in page.menu_links:
        target = urlsplit(href)
        response = client.get(target.path)
        assert response.status_code in (200, 302, 303, 503), href
        if target.fragment:
            assert target.fragment in _Page(response.get_data(as_text=True)).ids


def test_public_menu_points_private_account_links_to_hq(client, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "OAP_LOCAL_SERVICE_ROLE", "public")
    response = client.get("/pay/bank")
    assert response.status_code == 200
    for href, private in _Page(response.get_data(as_text=True)).menu_links:
        target = urlsplit(href)
        if private:
            assert target.scheme == "http"
            assert target.netloc == "127.0.0.1:5000"
        else:
            assert not target.netloc
            assert client.get(target.path).status_code == 200


def test_closed_capabilities_never_appear_as_live_menu_actions():
    sections = oap_pay.bank_menu_sections({})
    entries = {item["name"]: item for section in sections for item in section["items"]}
    for name in ("Transfers", "Cards", "Accounts", "Deposits", "Customer Funds", "SIKA value", "FX", "Cash / Post Office"):
        assert entries[name]["locked"] is True
        assert entries[name]["state"] == "Locked"
    sections = oap_pay.bank_menu_sections({"execute_payments": True})
    transfer = next(item for section in sections for item in section["items"] if item["name"] == "Transfers")
    assert transfer["state"] == "View status"


def test_activity_html_requires_sign_in(anonymous_client):
    response = anonymous_client.get("/pay/bank/me/transactions")
    assert response.status_code == 302
    assert "/enter-my-world" in response.headers["Location"]


def test_activity_html_uses_only_authenticated_owner_and_escapes_payee(client, monkeypatch):
    owners = []

    def activity(owner):
        owners.append(owner)
        return {"items": [{"payee_reference": "<script>untrusted</script>", "currency": "SIKA",
                           "amount": "12.00", "status": "PENDING", "created_at": "2026-11-22T10:00:00+00:00",
                           "payment_id": "request-1"}]}

    monkeypatch.setattr(oap_pay.sika_customer_view, "activity", activity)
    response = client.get("/pay/bank/me/transactions?owner_reference=other-person")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert owners == ["11111111-1111-4111-8111-111111111111"]
    page = response.get_data(as_text=True)
    assert "&lt;script&gt;untrusted&lt;/script&gt;" in page
    assert "<script>untrusted</script>" not in page
    assert "SIKA 12.00" in page
    assert "Pending" in page


def test_activity_failure_is_unavailable_not_empty_or_invented(client, monkeypatch):
    def unavailable(owner):
        raise oap_pay.sika_customer_view.CustomerViewUnavailable("unavailable")

    monkeypatch.setattr(oap_pay.sika_customer_view, "activity", unavailable)
    response = client.get("/pay/bank/me/transactions")
    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "no-store"
    assert "Activity unavailable" in response.get_data(as_text=True)
    assert "No recorded activity" not in response.get_data(as_text=True)
