"""No-network coverage of first-party HTTPS and private access gates."""
import runpy
from pathlib import Path

verify = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "deploy/selfhost/verify_koradaso_https.py")
)
check = verify["verify_release"]


def public_dns(host, port, **_kwargs):
    assert port == 443
    return [(2, 1, 6, "", ("8.8.8.8", 443))]


def test_real_public_and_private_behaviour_requires_both():
    calls = []
    def get(host, route):
        calls.append((host, route))
        if route == "/koradaso":
            return 200, ""
        return 302, "/auth/sign-in"
    result = check(
        "onanypostcode.global", "smi.onanypostcode.global",
        resolver=public_dns, get=get
    )
    assert result["status"] == "https_and_anonymous_boundary_passed"
    assert result["release_approved"] is False
    assert result["redmi_device_verified"] is False
    assert calls == [
        ("onanypostcode.global", "/koradaso"),
        ("smi.onanypostcode.global", "/mission/smi"),
    ]


def test_founder_dashboard_200_fails_closed():
    def get(host, route):
        return 200, ""
    result = check("onanypostcode.global", "smi.onanypostcode.global",
                   resolver=public_dns, get=get)
    assert result["status"] == "blocked"
    assert result["private_anonymous_denied"] is False


def test_redirect_to_external_or_non_login_denied():
    for redirect in ("https://evil.example/auth/sign-in", "/world", "http://smi.onanypostcode.global/login"):
        def get(host, route, *, selected_redirect=redirect):
            return (302, selected_redirect) if route == "/mission/smi" else (200, "")
        result = check("onanypostcode.global", "smi.onanypostcode.global",
                       resolver=public_dns, get=get)
        assert result["status"] == "blocked"


def test_missing_dns_and_same_host_fail_before_http():
    def fail_dns(host, port, **_kwargs):
        return [(2, 1, 6, "", ("127.0.0.1", 443))]
    for public, private, resolver in (
        ("onanypostcode.global", "onanypostcode.global", public_dns),
        ("localhost", "smi.onanypostcode.global", public_dns),
        ("onanypostcode.global", "smi.onanypostcode.global", fail_dns),
        ("on-any-postcode.onrender.com", "smi.onanypostcode.global", public_dns),
    ):
        result = check(public, private, resolver=resolver,
                       get=lambda *_args: (_ for _ in ()).throw(AssertionError("no network")))
        assert result["status"] == "blocked"
