"""Storage-aware, non-writing OAP Music metadata import planning.

This is an admission plan, NOT an importer or a reservation. The eventual
database writer must enforce limits and rights independently at write time.
"""
from __future__ import annotations

from mission_control.music_catalogue import estimate_metadata_bytes
from mission_control.oap_data_capacity import preflight_import

MAX_IMPORT_BATCH_RECORDS = 10_000


def plan_catalogue_batch(
    *,
    record_count: int,
    average_metadata_bytes: int = 1024,
) -> dict[str, object]:
    if isinstance(record_count, bool) or not isinstance(record_count, int):
        raise ValueError("invalid_record_count")
    if record_count < 0 or record_count > MAX_IMPORT_BATCH_RECORDS:
        raise ValueError("import_batch_limit_exceeded")
    raw_bytes = estimate_metadata_bytes(record_count, average_metadata_bytes)
    # Conservative overhead for database indexes, metadata expansion and staging.
    planned_bytes = raw_bytes * 3
    decision = preflight_import(requested_bytes=planned_bytes, system="music")
    return {
        "record_count": record_count,
        "raw_metadata_bytes": raw_bytes,
        "planned_bytes": planned_bytes,
        "write_authorized": False,
        "storage_preflight": decision,
    }
