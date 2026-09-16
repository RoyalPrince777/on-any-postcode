from __future__ import annotations

import smi_gateway


def test_normal_founder_repair_route_is_explicitly_allowed():
    assert smi_gateway._allowed("auth/repair-founder-password") is True


def test_public_signup_and_unrelated_auth_paths_stay_blocked():
    assert smi_gateway._allowed("auth/sign-up") is False
    assert smi_gateway._allowed("auth/admin-reset") is False
    assert smi_gateway._allowed("auth/debug") is False
