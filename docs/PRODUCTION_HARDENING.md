# SMI Production Hardening Guide

**Document Version**: 1.0  
**Last Updated**: 10 August 2026  
**Status**: READY FOR REVIEW

> **24 August 2026 implementation note:** The active Render slice now uses Neon
> Postgres for durable production records and Managed Neon Auth for private
> browser sessions. OAP World is public; My World, SMI and Mission Control are
> fail-closed behind the verified Neon UUID. The historical proposals below are
> retained for governance context and must not be mistaken for the active
> deployment procedure; use `.github/DEPLOYMENT.md` for the current release
> runbook.

---

## Executive Summary

The OAP SMI Digital Organism foundation patch is **architecturally sound** for governance-driven approval workflows, but requires critical hardening before production deployment:

1. **Database Migration** (SQLite → PostgreSQL)
2. **External Audit Sink** (Immutable off-database logging)
3. **Authentication Upgrade** (Bearer tokens → JWT + MFA)
4. **Observability** (Structured logging + metrics)
5. **Disaster Recovery** (Backup + failover strategy)

This document details each requirement with code examples, deployment procedures, and validation gates.

---

## 1. DATABASE MIGRATION: SQLite → PostgreSQL

### Why PostgreSQL?

- **Multi-instance HA**: Replication, failover, load balancing
- **Connection pooling**: PgBouncer or built-in sqlalchemy pools
- **Row-level security**: Audit isolation per tenant
- **ACID guarantees**: Stronger transactional semantics than SQLite
- **Monitoring**: pg_stat_statements, built-in metrics

### Implementation Steps

#### Step 1: Install dependencies

```bash
pip install --upgrade \
  sqlalchemy==2.0.23 \
  asyncpg==0.29.0 \
  alembic==1.13.0 \
  psycopg2-binary==2.9.9
```

#### Step 2: Update `oap/database.py`

**Before** (SQLite):
```python
class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
    
    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
```

**After** (PostgreSQL):
```python
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import asyncpg

class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections every hour
            echo=False,
        )
    
    def connect(self):
        return self.engine.connect()
    
    @contextmanager
    def transaction(self):
        connection = self.connect()
        try:
            with connection.begin():
                yield connection
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
```

#### Step 3: Create Alembic migrations

```bash
alembic init alembic
```

**`alembic/env.py`** - Configure PostgreSQL connection:

```python
import os
from sqlalchemy import engine_from_config, pool

config = context.config
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/oap_smi"
)
config.set_main_option("sqlalchemy.url", database_url)

engine = engine_from_config(
    config.get_section(config.config_ini_section),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,
)

with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
    context.configure(connection=connection, target_metadata=target_metadata)
```

**`alembic/versions/001_initial_schema.py`** - PostgreSQL schema:

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'identities',
        sa.Column('identity_id', sa.String(80), primary_key=True),
        sa.Column('identity_type', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('authority_level', sa.Integer, nullable=False),
        sa.Column('permissions_json', sa.Text, nullable=False),
        sa.Column('restrictions_json', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Index('idx_identities_status', 'status'),
    )
    
    op.create_table(
        'audit_events',
        sa.Column('sequence', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.String(80), nullable=False, unique=True),
        sa.Column('request_id', sa.String(80)),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('actor_id', sa.String(80), nullable=False),
        sa.Column('payload_json', sa.Text, nullable=False),
        sa.Column('previous_hash', sa.String(64), nullable=False),
        sa.Column('event_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Index('idx_audit_request', 'request_id', 'sequence'),
        sa.Index('idx_audit_actor', 'actor_id', 'created_at'),
    )

def downgrade():
    op.drop_table('audit_events')
    op.drop_table('identities')
```

#### Step 4: Run migrations

```bash
export DATABASE_URL="postgresql://oap:password@postgres.example.com:5432/oap_smi_prod"
alembic upgrade head
```

#### Step 5: Update environment configuration

**`oap/config.py`**:
```python
@dataclass(frozen=True, slots=True)
class Settings:
    environment: str = "development"
    database_url: str = "sqlite:///oap_smi.db"  # SQLite fallback for dev
    # ... rest of config
```

**`.env.example`**:
```bash
# SQLite (development only)
DATABASE_URL=sqlite:///oap_smi.db

# PostgreSQL (production)
# DATABASE_URL=postgresql://user:password@host:5432/oap_smi_prod
```

---

## 2. EXTERNAL IMMUTABLE AUDIT SINK

### Architecture

SQLite audit table → PostgreSQL → External Audit Sink (append-only)

### Implementation Options

#### Option A: AWS QLDB (Recommended for AWS users)

```python
import boto3
from datetime import datetime

class AWSQLDBAuditSink:
    def __init__(self, ledger_name: str):
        self.client = boto3.client('qldb')
        self.ledger_name = ledger_name
    
    def record(self, event: dict) -> str:
        """Send event to QLDB ledger (append-only, cryptographically verified)."""
        try:
            response = self.client.send_command(
                LedgerName=self.ledger_name,
                Statement=(
                    'INSERT INTO audit_events ?'
                ),
                Parameters=[event],
            )
            return response['DocumentId']
        except Exception as e:
            logger.error(f"QLDB audit sink error: {e}", extra={"event_id": event.get('event_id')})
            raise
```

#### Option B: HashiCorp Vault (Recommended for on-premise)

```python
import hvac
import json

class VaultAuditSink:
    def __init__(self, vault_addr: str, vault_token: str):
        self.client = hvac.Client(url=vault_addr, token=vault_token)
    
    def record(self, event: dict) -> str:
        """Write event to Vault's audit backend (append-only)."""
        try:
            path = f"audit-trail/{event['event_id']}"
            self.client.secrets.kv.create_or_update_secret(
                path=path,
                secret_dict=event,
                cas=0,  # Ensure it's created only once
            )
            return event['event_id']
        except Exception as e:
            logger.error(f"Vault audit sink error: {e}")
            raise
```

#### Option C: Syslog-NG with TLS (On-premise)

```python
import socket
import ssl
import json
from datetime import datetime

class SyslogNGAuditSink:
    def __init__(self, host: str, port: int, cert_path: str, key_path: str):
        self.host = host
        self.port = port
        self.cert_path = cert_path
        self.key_path = key_path
    
    def record(self, event: dict) -> str:
        """Send event to syslog-ng via TLS."""
        try:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.load_cert_chain(self.cert_path, self.key_path)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                with context.wrap_socket(sock, server_hostname=self.host) as ssock:
                    ssock.connect((self.host, self.port))
                    
                    # RFC 5424 syslog format
                    timestamp = datetime.utcnow().isoformat()
                    syslog_msg = f"<134>1 {timestamp} oap-smi {event['event_type']} - - {json.dumps(event)}"
                    ssock.sendall(syslog_msg.encode('utf-8'))
            
            return event['event_id']
        except Exception as e:
            logger.error(f"Syslog-NG audit sink error: {e}")
            raise
```

### Integration into AuditLogger

**`oap/audit/logger.py`**:

```python
from oap.audit.sinks import AWSQLDBAuditSink

class AuditLogger:
    def __init__(self, database: Database, external_sink=None):
        self.database = database
        self.external_sink = external_sink  # AWS QLDB, Vault, or Syslog
    
    def record(
        self,
        event_type: str,
        actor_id: str,
        payload: dict,
        request_id: str | None = None,
    ) -> dict:
        # Write to primary database
        event = self._write_to_db(event_type, actor_id, payload, request_id)
        
        # Send to external audit sink (asynchronously to avoid blocking)
        if self.external_sink:
            try:
                # Fire-and-forget with retry logic
                self._send_to_external_sink(event)
            except Exception as e:
                logger.error(f"External audit sink failed: {e}", extra={"event_id": event['event_id']})
                # Continue processing—primary DB is source of truth
        
        return event
    
    def _send_to_external_sink(self, event: dict):
        """Send to external sink with exponential backoff retry."""
        for attempt in range(3):
            try:
                self.external_sink.record(event)
                return
            except Exception as e:
                if attempt < 2:
                    sleep_time = 2 ** attempt
                    logger.warning(f"Audit sink retry in {sleep_time}s: {e}")
                    time.sleep(sleep_time)
                else:
                    raise
```

---

## 3. AUTHENTICATION UPGRADE: JWT + MFA

### Current Issue

Bearing token in `X-OAP-Human-Token` header:
- No expiration
- No MFA
- Not cryptographically bound to session

### Solution: JWT with RS256 + MFA

**Install dependencies**:
```bash
pip install --upgrade \
  PyJWT==2.8.1 \
  cryptography==41.0.7 \
  python-jose==3.3.0 \
  passlib==1.7.4 \
  python-multipart==0.0.6
```

**`oap/security/jwt.py`** - JWT token generation and validation:

```python
from datetime import datetime, timedelta, timezone
import jwt
from typing import Optional

class JWTHandler:
    def __init__(self, private_key_path: str, public_key_path: str):
        with open(private_key_path, 'r') as f:
            self.private_key = f.read()
        with open(public_key_path, 'r') as f:
            self.public_key = f.read()
    
    def create_token(
        self,
        identity_id: str,
        authority_level: int,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create JWT token for Human Authority."""
        if expires_delta is None:
            expires_delta = timedelta(hours=1)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": identity_id,
            "authority_level": authority_level,
            "iat": datetime.now(timezone.utc),
            "exp": expire,
            "type": "access",
        }
        
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256"
        )
        
        return token
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
```

**`oap/security/mfa.py`** - MFA enforcement:

```python
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAHandler:
    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret for MFA."""
        return pyotp.random_base32()
    
    @staticmethod
    def get_provisioning_uri(secret: str, name: str, issuer: str) -> str:
        """Generate provisioning URI for QR code."""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=name, issuer_name=issuer)
    
    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """Generate QR code as base64 PNG."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_totp(secret: str, code: str) -> bool:
        """Verify TOTP code (allow 30-second window for clock drift)."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
```

**`oap/main.py`** - Update Human Authority authentication:

```python
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from oap.security.jwt import JWTHandler
from oap.security.mfa import MFAHandler

bearer_scheme = HTTPBearer()
jwt_handler = JWTHandler(
    private_key_path="/etc/oap/keys/private.pem",
    public_key_path="/etc/oap/keys/public.pem"
)

def human_authority(
    credentials: HTTPAuthCredentials = Depends(bearer_scheme),
    mfa_code: str = Header(None),
    container: OrganismContainer = Depends(organism),
) -> str:
    """Verify Human Authority JWT + MFA."""
    try:
        payload = jwt_handler.verify_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    
    identity_id = payload["sub"]
    authority_level = payload["authority_level"]
    
    if authority_level != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only level-zero Human Authority allowed"
        )
    
    # Verify MFA
    identity = container.identity.get_record(identity_id)
    if not identity or not identity.get("mfa_secret"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA not enabled for this identity"
        )
    
    if not MFAHandler.verify_totp(identity["mfa_secret"], mfa_code or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code"
        )
    
    return identity_id
```

---

## 4. RATE LIMITING & REQUEST CORRELATION

**`oap/middleware/security.py`**:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger("oap.security")

class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Add request ID if not present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "client_ip": request.client.host if request.client else "unknown",
            }
        )
        return response

# Apply rate limits
@app.post("/run", tags=["smi"])
@limiter.limit("10/minute")
def run_smi(request: Request, payload: RunRequest, ...):
    return container.smi.process(payload)

@app.post("/approvals/{approval_id}/approve", tags=["human-authority"])
@limiter.limit("30/minute")
def approve(request: Request, ...):
    ...
```

---

## 5. STRUCTURED LOGGING

**`oap/logging_config.py`**:

```python
import logging
import logging.config
import json
from pythonjsonlogger import jsonlogger

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()":  "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(timestamp)s %(level)s %(name)s %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "/var/log/oap/smi.log",
            "maxBytes": 104857600,  # 100MB
            "backupCount": 10,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

---

## 6. HEALTH CHECKS

**`oap/health.py`**:

```python
from enum import Enum
from datetime import datetime

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck:
    def __init__(self, container: OrganismContainer):
        self.container = container
    
    def check(self) -> dict:
        now = datetime.utcnow().isoformat()
        checks = {
            "database": self._check_database(),
            "audit_chain": self._check_audit_chain(),
            "approval_security": self._check_approval_security(),
            "registry": self._check_registry(),
        }
        
        overall = "healthy" if all(c["ok"] for c in checks.values()) else "degraded"
        
        return {
            "timestamp": now,
            "status": overall,
            "checks": checks,
        }
    
    def _check_database(self) -> dict:
        try:
            result = self.container.database.fetch_one("SELECT 1")
            return {"ok": result is not None, "message": "Database connection OK"}
        except Exception as e:
            return {"ok": False, "message": f"Database error: {str(e)}"}
    
    def _check_audit_chain(self) -> dict:
        try:
            verification = self.container.audit.verify_chain()
            return {
                "ok": verification["valid"],
                "message": f"Audit chain: {verification['checked']} events verified"
            }
        except Exception as e:
            return {"ok": False, "message": f"Audit chain error: {str(e)}"}
    
    def _check_approval_security(self) -> dict:
        ready = self.container.settings.approval_ready
        return {
            "ok": ready,
            "message": "Approval security configured" if ready else "Approval security NOT configured"
        }
    
    def _check_registry(self) -> dict:
        try:
            validation = self.container.registry.validate()
            return {
                "ok": validation["valid"],
                "message": validation.get("summary", "Registry validation OK")
            }
        except Exception as e:
            return {"ok": False, "message": f"Registry error: {str(e)}"}
```

---

## PRODUCTION DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] **Database**
  - [ ] PostgreSQL cluster HA configured (primary + 2 replicas)
  - [ ] Connection pooling (PgBouncer or sqlalchemy) tested
  - [ ] Backup strategy implemented + tested (24h RPO, 1h RTO)
  - [ ] Alembic migrations applied to production schema
  - [ ] Point-in-time recovery (PITR) enabled

- [ ] **Audit Sink**
  - [ ] External audit sink (AWS QLDB / Vault / Syslog-NG) provisioned
  - [ ] TLS certificates generated and deployed
  - [ ] Retry logic tested with simulated failures
  - [ ] Audit trail verified against primary database

- [ ] **Authentication**
  - [ ] JWT RS256 key pair generated and securely stored
  - [ ] MFA enabled for all Human Authority identities
  - [ ] Token rotation strategy documented
  - [ ] MFA recovery codes generated and secured

- [ ] **Security**
  - [ ] CORS origins locked to specific trusted hosts (NO wildcards)
  - [ ] Rate limiting thresholds validated under load
  - [ ] Request correlation middleware enabled
  - [ ] All secrets stored in AWS Secrets Manager / Vault
  - [ ] .env files deleted from version control
  - [ ] Security scan passed (OWASP Top 10, Bandit)

- [ ] **Observability**
  - [ ] Structured logging to centralized sink (ELK / Datadog)
  - [ ] Prometheus metrics scraped by monitoring system
  - [ ] Alert rules configured for approval failures, audit chain breaks
  - [ ] Dashboards created (health, approvals, audit)
  - [ ] Log retention policy set (90 days minimum)

- [ ] **Testing**
  - [ ] Load testing: 100+ concurrent approval flows
  - [ ] Chaos test: Database failover, approval timeout, Guardian reject
  - [ ] Audit chain forensic verification passed
  - [ ] Replay attack test passed (single-use token enforcement)
  - [ ] Token expiration boundary test passed

- [ ] **Documentation**
  - [ ] Runbooks created (incident response, rollback, recovery)
  - [ ] Deployment guide updated with new PostgreSQL steps
  - [ ] API documentation (OpenAPI/Swagger) up-to-date
  - [ ] Architecture diagram updated
  - [ ] Change log documented

### Go/No-Go Decision Gate

**All items must be checked before production deployment.**

---

## INCIDENT RESPONSE RUNBOOKS

### Runbook 1: Approval Token Expired

**Symptom**: User receives "APPROVAL_EXPIRED" error  
**Root Cause**: Token not consumed within TTL window  
**Resolution**:

```bash
# 1. Check approval status
SELECT * FROM human_approvals WHERE approval_id = 'APR-xxx';

# 2. If still APPROVED, issue new token
POST /approvals/{approval_id}/approve
  X-OAP-Human-Token: <human_token>
  Content-Type: application/json
  { "reason": "Token expired, reissued" }

# 3. Alert on recurrence:
alert if token_expiry_errors > 5 in 1 hour
```

### Runbook 2: Audit Chain Break Detected

**Symptom**: `audit.verify_chain()` returns `"valid": false`  
**Root Cause**: Database tampering or corruption  
**Resolution**:

```bash
# 1. IMMEDIATELY isolate instance
sudo systemctl stop oap-smi

# 2. Capture state for forensics
mysql ... > audit_events_corrupted.sql

# 3. Failover to replica
PROMOTE REPLICA to primary

# 4. Restore application
sudo systemctl start oap-smi

# 5. Verify audit chain on replica
GET /audit/verify

# 6. Post-incident: Re-verify all external audit sink records
```

### Runbook 3: Human Authority MFA Lost

**Symptom**: Human Authority cannot approve (MFA code fails)  
**Root Cause**: TOTP device lost or clock skew  
**Resolution**:

```bash
# 1. Verify identity ownership (secondary authentication)
# Contact Human Authority with pre-registered recovery questions

# 2. Generate new MFA secret
POST /admin/identity/HUMAN-001/mfa/reset
  X-Admin-Token: <admin_override_token>

# 3. Issue new QR code

# 4. Test with new device

# 5. Log incident for audit
```

---

## References

- [PostgreSQL HA Documentation](https://www.postgresql.org/docs/current/)
- [AWS QLDB](https://docs.aws.amazon.com/qldb/)
- [OWASP FastAPI Security](https://cheatsheetseries.owasp.org/cheatsheets/FastAPI_Security_Cheat_Sheet.html)
- [RFC 7519 - JWT](https://tools.ietf.org/html/rfc7519)
- [RFC 6238 - TOTP](https://tools.ietf.org/html/rfc6238)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
