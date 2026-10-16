"""Founder-gated OAP Domains canonical SQLite records; no live registrar calls."""
import json, re, sqlite3, uuid
from datetime import datetime, timezone
from typing import Protocol

class RegistrarProvider(Protocol):
    def availability(self, domain: str) -> dict: ...
    def exact_price(self, domain: str) -> dict: ...
    def register(self, domain: str, authorization: dict) -> dict: ...
    def rdap_evidence(self, domain: str) -> dict: ...
    def dns_control(self, domain: str) -> dict: ...

class ExecutionDisabled(RuntimeError): pass
class DisabledRegistrar:
    def availability(self, domain): raise ExecutionDisabled("Registrar not connected")
    def exact_price(self, domain): raise ExecutionDisabled("Registrar not connected")
    def register(self, domain, authorization): raise ExecutionDisabled("Registration disabled")
    def rdap_evidence(self, domain): raise ExecutionDisabled("Registrar not connected")
    def dns_control(self, domain): raise ExecutionDisabled("Registrar not connected")

TRANSITIONS={"draft":{"quoted"},"quoted":{"checkout_authorized"},"checkout_authorized":{"registration_pending"},"registration_pending":{"registered","registration_failed"},"registered":{"owned"},"registration_failed":{"quoted"},"owned":set()}
REQUIRED={"quoted":"exact_price","checkout_authorized":"checkout","registration_pending":"checkout","registered":"registrar_registration","owned":"dns_control"}
def stamp(): return datetime.now(timezone.utc).isoformat()
def normalize(name):
    if not isinstance(name,str): raise ValueError("domain must be text")
    try: name=name.strip().rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as e: raise ValueError("invalid domain") from e
    if len(name)>253 or not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",name): raise ValueError("invalid domain")
    return name

class DomainCore:
    def __init__(self, database, provider=None, execution_enabled=False):
        self.db=sqlite3.connect(database)
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.provider=provider or DisabledRegistrar()
        self.execution_enabled=False  # fail closed until a real registrar execution integration is reviewed
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS domains (id TEXT PRIMARY KEY,name TEXT UNIQUE NOT NULL,owner_id TEXT NOT NULL,state TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS domain_evidence (id INTEGER PRIMARY KEY AUTOINCREMENT,domain_id TEXT NOT NULL REFERENCES domains(id),kind TEXT NOT NULL,source TEXT NOT NULL,payload TEXT NOT NULL,recorded_at TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS ownership_ledger (id INTEGER PRIMARY KEY AUTOINCREMENT,domain_id TEXT NOT NULL REFERENCES domains(id),owner_id TEXT NOT NULL,event TEXT NOT NULL,evidence_id INTEGER REFERENCES domain_evidence(id),recorded_at TEXT NOT NULL);
        """)
        self.db.commit()
    def get(self, record_id):
        row=self.db.execute("SELECT * FROM domains WHERE id=?",(record_id,)).fetchone()
        return dict(row) if row else None
    def create(self, name, owner_id):
        name=normalize(name)
        if not isinstance(owner_id,str) or not owner_id.strip(): raise ValueError("owner required")
        rid=uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO domains VALUES (?,?,?,?,?,?)",(rid,name,owner_id,"draft",stamp(),stamp()))
            self.db.execute("INSERT INTO ownership_ledger(domain_id,owner_id,event,recorded_at) VALUES (?,?,?,?)",(rid,owner_id,"claim_created_not_registry_ownership",stamp()))
        return self.get(rid)
    def mine(self, owner_id):
        return [dict(r) for r in self.db.execute("SELECT * FROM domains WHERE owner_id=? ORDER BY created_at DESC",(owner_id,))]
    def market(self):
        return []  # Resale proof gate not implemented. No invented listings.
    def evidence(self, rid, kind, source, payload):
        if not self.get(rid): raise KeyError(rid)
        if kind not in {"availability","exact_price","checkout","registrar_registration","registry_rdap","dns_control"}: raise ValueError("evidence kind")
        if not source or not isinstance(payload,dict): raise ValueError("source/payload required")
        with self.db:
            cursor=self.db.execute("INSERT INTO domain_evidence(domain_id,kind,source,payload,recorded_at) VALUES (?,?,?,?,?)",(rid,kind,source,json.dumps(payload,sort_keys=True),stamp()))
        return cursor.lastrowid
    def transition(self,rid,target,evidence_id):
        row=self.get(rid)
        if row is None: raise KeyError(rid)
        if target not in TRANSITIONS[row["state"]]: raise ValueError("invalid transition")
        if target in {"checkout_authorized","registration_pending","registered","owned"}: raise ExecutionDisabled("Live payment and registrar proof gate closed")
        if target in REQUIRED:
            evidence=self.db.execute("SELECT kind FROM domain_evidence WHERE id=? AND domain_id=?",(evidence_id,rid)).fetchone()
            if not evidence or evidence["kind"]!=REQUIRED[target]: raise ValueError("missing evidence")
            if target in {"registration_pending","registered","owned"}: raise ExecutionDisabled("registration gate closed")
            if target=="owned":
                kinds={r[0] for r in self.db.execute("SELECT kind FROM domain_evidence WHERE domain_id=?",(rid,))}
                if not {"availability","exact_price","checkout","registrar_registration","registry_rdap","dns_control"} <= kinds: raise ValueError("incomplete ownership proof")
        with self.db:
            self.db.execute("UPDATE domains SET state=?,updated_at=? WHERE id=?",(target,stamp(),rid))
            self.db.execute("INSERT INTO ownership_ledger(domain_id,owner_id,event,evidence_id,recorded_at) VALUES (?,?,?,?,?)",(rid,row["owner_id"],"state:"+target,evidence_id,stamp()))
        return self.get(rid)
    def register(self,rid,authorization): raise ExecutionDisabled("No registrar execution wired")
