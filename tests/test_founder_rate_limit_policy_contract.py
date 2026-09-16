from pathlib import Path


def test_founder_sign_in_failure_policy_is_documented():
    policy = Path("docs/FOUNDERS_RATE_LIMIT_GOVERNANCE.md").read_text(encoding="utf-8")
    assert "count only genuine credential rejections" in policy
    assert "Infrastructure/provider failures do not consume" in policy
    assert "Successful sign-in clears" in policy
