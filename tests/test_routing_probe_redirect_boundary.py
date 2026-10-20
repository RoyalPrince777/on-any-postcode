"""Live routing checks must reject HTTP redirects."""
from urllib import error, request
import pytest
from scripts import routing_live_green_gate as gate


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_probe_rejects_redirect(status):
    original = request.Request("https://routing.example.org/route/v1/driving/1,2;3,4")
    with pytest.raises(error.HTTPError):
        gate._RejectRedirects().redirect_request(
            original, None, status, "redirect",
            {"Location": "https://other.example.org/"}, "https://other.example.org/"
        )
