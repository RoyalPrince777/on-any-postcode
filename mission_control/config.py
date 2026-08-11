# mission_control/config.py
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Repository root: assume this file lives under mission_control/ within repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent

# 1) Canonical DB path
OAP_DATABASE_PATH = os.environ.get("OAP_DATABASE_PATH")
if OAP_DATABASE_PATH:
    db_path = Path(OAP_DATABASE_PATH)
    if not db_path.is_absolute():
        raise RuntimeError("OAP_DATABASE_PATH must be an absolute path")
else:
    db_path = REPO_ROOT / "oap.db"

# normalized absolute path
OAP_DATABASE_PATH = str(db_path.resolve())
logger.info(f"Resolved OAP database path: {OAP_DATABASE_PATH}")

# 2) Backup dir
OAP_BACKUP_DIR = os.environ.get("OAP_BACKUP_DIR")
if OAP_BACKUP_DIR:
    backup_dir = Path(OAP_BACKUP_DIR)
    if not backup_dir.is_absolute():
        raise RuntimeError("OAP_BACKUP_DIR must be an absolute path")
else:
    backup_dir = Path(OAP_DATABASE_PATH).parent / "backups"

OAP_BACKUP_DIR = str(backup_dir.resolve())

# 3) MFA encryption key
OAP_MFA_ENC_KEY = os.environ.get("OAP_MFA_ENC_KEY")

# 4) RS256 key paths and JWT settings (Option B)
OAP_JWT_PUBLIC_KEY_PATH = os.environ.get("OAP_JWT_PUBLIC_KEY_PATH")
OAP_JWT_PRIVATE_KEY_PATH = os.environ.get("OAP_JWT_PRIVATE_KEY_PATH")
OAP_JWT_ISSUER = os.environ.get("OAP_JWT_ISSUER", "on-any-postcode")
OAP_JWT_AUDIENCE = os.environ.get("OAP_JWT_AUDIENCE", "oap-sovereign-mission-control")
OAP_JWT_ACTIVE_KID = os.environ.get("OAP_JWT_ACTIVE_KID")
OAP_JWT_ACCESS_TTL_SECONDS = int(os.environ.get("OAP_JWT_ACCESS_TTL_SECONDS", "900"))

# Emergency / Safe Mode permission names
PERM_EMERGENCY_PAUSE_ACTIVATE = "EMERGENCY_PAUSE_ACTIVATE"
PERM_EMERGENCY_PAUSE_RELEASE = "EMERGENCY_PAUSE_RELEASE"
PERM_SAFE_MODE_ACTIVATE = "SAFE_MODE_ACTIVATE"
PERM_SAFE_MODE_RELEASE = "SAFE_MODE_RELEASE"

# Two-person approval configuration
# Configurable via env var; if empty, default to requiring two persons only when explicitly set on approval
TWO_PERSON_ENABLED = os.environ.get("OAP_TWO_PERSON_ENABLED", "false").lower() == "true"

# Ollama adapter
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# Local mode flag
OAP_LOCAL_MODE = os.environ.get("OAP_LOCAL_MODE", "true").lower() == "true"

