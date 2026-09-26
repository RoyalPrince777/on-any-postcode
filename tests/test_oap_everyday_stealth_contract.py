"""Offline negative tests for isolated stealth creative contract."""
import unittest

from mission_control.oap_everyday_stealth_contract import (
    FREE_CAPACITY, PACKAGES, State, StealthCreative,
)


class StealthCreativeTests(unittest.TestCase):
    def test_fixed_prices(self):
        self.assertEqual({p: v[0] for p, v in PACKAGES.items()},
                         {"free": 0, "quick": 25, "starter": 75, "plus": 150})

    def test_capacity_idempotency_and_collision(self):
        service = StealthCreative()
        for i in range(FREE_CAPACITY):
            order = service.request(f"free-{i}", "free")
            self.assertIs(order, service.request(f"free-{i}", "free"))
        with self.assertRaises(ValueError):
            service.request("free-extra", "free")
        with self.assertRaises(ValueError):
            service.request("free-0", "plus")

    def test_rejects_pii_reference_and_unknown_package(self):
        service = StealthCreative()
        for reference, package in [("person@example.com", "free"),
                                   ("", "free"), ("abc", "nonexistent")]:
            with self.assertRaises(ValueError):
                service.request(reference, package)

    def test_paid_fail_closed_until_evidence(self):
        service = StealthCreative()
        service.request("paid-1", "starter")
        with self.assertRaises(PermissionError):
            service.advance("paid-1", founder=False)
        self.assertEqual(service.advance("paid-1", founder=True).state,
                         State.BRIEF_APPROVED)
        with self.assertRaises(PermissionError):
            service.advance("paid-1", founder=True)
        service.advance("paid-1", founder=True, rights=True)
        with self.assertRaises(PermissionError):
            service.advance("paid-1", founder=True)
        service.advance("paid-1", founder=True, payment=True)
        self.assertEqual(service.advance("paid-1", founder=True).state,
                         State.DELIVERED)

    def test_free_does_not_require_payment(self):
        service = StealthCreative()
        service.request("free-1", "free")
        service.advance("free-1", founder=True)
        service.advance("free-1", founder=True, rights=True)
        order = service.advance("free-1", founder=True)
        self.assertEqual(order.state, State.PAYMENT_CONFIRMED)
        self.assertFalse(order.payment_evidence)

    def test_stop_and_independent_recovery(self):
        service = StealthCreative()
        service.request("item-1", "quick")
        with self.assertRaises(PermissionError):
            service.stop(founder=False)
        service.stop(founder=True)
        with self.assertRaises(PermissionError):
            service.request("item-2", "quick")
        with self.assertRaises(PermissionError):
            service.advance("item-1", founder=True)
        with self.assertRaises(PermissionError):
            service.recover(founder=True, independent_evidence=False)
        with self.assertRaises(PermissionError):
            service.recover(founder=False, independent_evidence=True)
        service.recover(founder=True, independent_evidence=True)
        service.request("item-2", "quick")


if __name__ == "__main__":
    unittest.main()
