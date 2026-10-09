"""Colonel Hathi: read-only Founder storage status aggregation.

A report is evidence only; it never provisions storage or proves a restore.
"""
from __future__ import annotations

from mission_control.oap_data_capacity import configured_storage_capacity
from mission_control.oap_data_hathi import StorageEvidence, hathi_assessment


def founder_storage_report() -> dict[str, object]:
    capacity = configured_storage_capacity()
    assessment = hathi_assessment(
        StorageEvidence(
            capacity_measured=capacity is not None,
            backup_verified=False,
            restore_test_passed=False,
            integrity_check_passed=False,
        )
    )
    return {
        "storage": {
            "measured": capacity is not None,
            "total_bytes": capacity.total_bytes if capacity else None,
            "used_bytes": capacity.used_bytes if capacity else None,
            "free_bytes": capacity.free_bytes if capacity else None,
        },
        "hathi": assessment,
        "production_ready": False,
        "note": "Report-only. Backup, restore and integrity remain unverified until connected to independent evidence.",
    }
