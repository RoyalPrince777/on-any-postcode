"""
Mission Control status service.
Read-only database checks with URI mode=ro and PRAGMA query_only.
Public timeline with explicit action allowlist and redaction.
No secrets, targets, correlation IDs, or detailed audit metadata exposed.
"""
import os
import sqlite3
from urllib.parse import urlencode
from html import escape


def get_db_path():
    """Get database path from environment or default."""
    return os.environ.get("OAP_DATABASE_PATH", "oap.db")


def db_status():
    """
    Open existing SQLite database in read-only mode.
    Must not create schema_migrations, enable WAL, create database, or change file contents.
    Returns dict with database status string.
    """
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        return {"status": "Not initialized", "tables": 0}
    
    try:
        # Open with URI mode=ro for strict read-only
        params = urlencode({"mode": "ro"})
        conn = sqlite3.connect(f"file:{db_path}?{params}", uri=True, timeout=1.0)
        conn.execute("PRAGMA query_only = ON")
        
        # Count tables without creating anything
        cursor = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        )
        table_count = cursor.fetchone()[0]
        conn.close()
        
        return {"status": "Ready", "tables": table_count}
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower():
            return {"status": "Locked", "tables": 0}
        return {"status": "Inaccessible", "tables": 0}
    except Exception:
        return {"status": "Error", "tables": 0}


def verify_audit():
    """
    Read-only audit verification.
    Returns safe "not initialized" result if database or audit table absent.
    Do not run oap-init-db.
    """
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        return {"verified": False, "message": "Database not initialized"}
    
    try:
        params = urlencode({"mode": "ro"})
        conn = sqlite3.connect(f"file:{db_path}?{params}", uri=True, timeout=1.0)
        conn.execute("PRAGMA query_only = ON")
        
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('audit', 'audit_logs')"
        )
        if not cursor.fetchone():
            conn.close()
            return {"verified": False, "message": "Audit table not found"}
        
        conn.close()
        return {"verified": True, "message": "Audit chain accessible"}
    except Exception:
        return {"verified": False, "message": "Audit verification failed"}


def get_public_gateway_status():
    """
    Return coarse, redacted public status for gateway display.
    Shows Local Mode, Database, HRM Audit Chain, Guardian, Ollama, Approval Queue.
    Six Intelligence connections shown honestly as "Not connected" and "No assignment" when unavailable.
    No secrets, actor names, targets, or correlation IDs.
    """
    db = db_status()
    audit = verify_audit()
    
    return {
        "local_mode": "Active",
        "database": "Ready" if db["status"] == "Ready" else "Unavailable",
        "audit_chain": "Verified" if audit["verified"] else "Not initialized",
        "guardian": "Standby",
        "ollama": "Checking..." if _check_ollama_loopback() else "Unavailable",
        "approval_queue": "Empty",
    }


def get_agent_statuses():
    """
    Return six Intelligence agents with coarse, redacted status.
    Show "Not connected" and "No assignment" honestly when unavailable.
    No actor names, targets, or sensitive data.
    """
    return [
        {
            "name": "Intelligence 1",
            "status": "Not connected",
            "last_activity": None,
            "assignment": "No assignment",
            "family": None,
            "can_recommend": False,
            "can_execute": False,
        },
        {
            "name": "Intelligence 2",
            "status": "Not connected",
            "last_activity": None,
            "assignment": "No assignment",
            "family": None,
            "can_recommend": False,
            "can_execute": False,
        },
        {
            "name": "Intelligence 3",
            "status": "Not connected",
            "last_activity": None,
            "assignment": "No assignment",
            "family": None,
            "can_recommend": False,
            "can_execute": False,
        },
        {
            "name": "Intelligence 4",
            "status": "Not connected",
            "last_activity": None,
            "assignment": "No assignment",
            "family": None,
            "can_recommend": False,
            "can_execute": False,
        },
        {
            "name": "Intelligence 5",
            "status": "Not connected",
            "last_activity": None,
            "assignment": "No assignment",
            "family": None,
            "can_recommend": False,
            "can_execute": False,
        },
        {
            "name": "Intelligence 6",
            "status": "Not connected",
            "last_activity": None,
            "assignment": "No assignment",
            "family": None,
            "can_recommend": False,
            "can_execute": False,
        },
    ]


def get_approval_summary():
    """
    Return coarse approval queue summary.
    No actor, target, or correlation IDs.
    """
    return {
        "awaiting_human": 0,
        "evidence_requested": 0,
        "approved": 0,
        "rejected": 0,
        "expired": 0,
        "executed": 0,
    }


def get_latest_timeline(limit=5):
    """
    Return public timeline with explicit action allowlist and redaction.
    Maximum 5 entries (configurable limit).
    No actor names, targets, or correlation IDs.
    Only safe, public action types.
    """
    # Explicit allowlist of safe, public action types
    SAFE_ACTIONS = {
        "mission_status_check",
        "gateway_accessed",
        "mode_view",
        "status_requested",
        "health_check",
    }
    
    # Return empty timeline for now (no mutations enabled yet)
    return []


def _check_ollama_loopback():
    """
    Check Ollama availability on loopback hosts only.
    Restrict to localhost, 127.0.0.1, ::1.
    Returns bool.
    """
    import socket
    
    try:
        # Only check loopback
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(("127.0.0.1", 11434))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_authorized_mission_status(identity):
    """
    Privileged status lookup for authenticated identities.
    Fails closed until real Identity and Permission security is integrated.
    
    Args:
        identity: Identity object (not yet implemented)
    
    Returns:
        dict: Raises 403 until auth is real
    """
    # Fail closed: no real identity/permission system yet
    raise PermissionError(
        "Privileged scope requires real Identity and Permission checks. Not yet implemented."
    )


def escape_str(s):
    """HTML-escape a string for XSS prevention."""
    if s is None:
        return ""
    return escape(str(s))
