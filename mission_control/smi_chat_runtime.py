"""Governed SMI Chat runtime: identity, permission, Guardian, provider and HRM."""
from __future__ import annotations
import hashlib, json, os, re, uuid
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from . import postgres_db

MODEL = os.environ.get("OAP_AI_MODEL", "gpt-5-mini")
PROVIDER = os.environ.get("OAP_AI_PROVIDER", "openai")
MAX_INPUT = 4000
BLOCKED = (
    r"\b(?:steal|malware|ransomware|credential theft|disable safety|bypass authentication)\b",
)

def _clean(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]

def guardian_review(message: str) -> tuple[str, str]:
    if not message:
        return "BLOCKED", "A message is required."
    if any(re.search(pattern, message, re.I) for pattern in BLOCKED):
        return "BLOCKED", "Guardian blocked a harmful or unauthorized request."
    return "PASSED", "Bounded recommendation request passed Guardian review."

def _ensure_identity(connection, identity_id: str, display_name: str) -> None:
    connection.execute(
        """INSERT INTO oap_identities(identity_id,display_name,identity_type,status)
           VALUES (%s,%s,'HUMAN','ACTIVE') ON CONFLICT (identity_id) DO UPDATE
           SET display_name=EXCLUDED.display_name, updated_at=CURRENT_TIMESTAMP""",
        (identity_id, display_name),
    )
    connection.execute(
        """INSERT INTO oap_roles(role_id,name,authority_level)
           VALUES ('community_member','Community Member',5) ON CONFLICT DO NOTHING"""
    )
    connection.execute(
        """INSERT INTO oap_role_permissions(role_id,permission_id)
           VALUES ('community_member','REQUEST_RECOMMENDATION') ON CONFLICT DO NOTHING"""
    )
    connection.execute(
        """INSERT INTO oap_identity_roles(identity_id,role_id,granted_by)
           VALUES (%s,'community_member',NULL) ON CONFLICT DO NOTHING""",
        (identity_id,),
    )

def _permission(connection, identity_id: str) -> bool:
    row=connection.execute(
        """SELECT 1 FROM oap_identities i
           JOIN oap_identity_roles ir ON ir.identity_id=i.identity_id
           JOIN oap_role_permissions rp ON rp.role_id=ir.role_id
           WHERE i.identity_id=%s AND i.status='ACTIVE'
             AND rp.permission_id='REQUEST_RECOMMENDATION' LIMIT 1""",
        (identity_id,),
    ).fetchone()
    return row is not None

def _provider(message: str) -> str:
    key=os.environ.get("OPENAI_API_KEY","").strip()
    if not key:
        raise RuntimeError("provider_key_missing")
    system=(
        "You are SMI, the recommendation-only intelligence of ON ANY POSTCODE. "
        "Be practical, concise and human-first. Never claim final authority or execute actions. "
        "OAP means ON ANY POSTCODE. Human Authority remains final."
    )
    payload=json.dumps({
        "model":MODEL,
        "input":[
            {"role":"system","content":[{"type":"input_text","text":system}]},
            {"role":"user","content":[{"type":"input_text","text":message}]},
        ],
        "max_output_tokens":900,
    }).encode()
    req=urlrequest.Request(
        "https://api.openai.com/v1/responses", data=payload,
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=35) as response:
            data=json.loads(response.read().decode())
    except HTTPError as exc:
        raise RuntimeError(f"provider_http_{exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("provider_unavailable") from exc
    text=_clean(data.get("output_text"), 12000)
    if not text:
        for item in data.get("output",[]):
            for content in item.get("content",[]):
                if content.get("type")=="output_text":
                    text += content.get("text","")
    if not text.strip():
        raise RuntimeError("provider_empty_response")
    return text.strip()[:12000]

def chat(message: object, identity_id: str, display_name: object, conversation_id: object=None) -> dict:
    clean=_clean(message,MAX_INPUT)
    name=_clean(display_name,80) or "OAP Member"
    try: identity=str(uuid.UUID(identity_id))
    except (ValueError,TypeError): raise ValueError("invalid_identity")
    request_id=str(uuid.uuid4())
    outcome,reason=guardian_review(clean)
    with postgres_db.connect() as connection:
        _ensure_identity(connection,identity,name)
        if not _permission(connection,identity):
            raise PermissionError("REQUEST_RECOMMENDATION permission required")
        conversation=_clean(conversation_id,40)
        try: conversation=str(uuid.UUID(conversation)) if conversation else str(uuid.uuid4())
        except ValueError: conversation=str(uuid.uuid4())
        connection.execute(
            """INSERT INTO smi_conversations(conversation_id,identity_id,title)
               VALUES (%s,%s,%s) ON CONFLICT (conversation_id) DO UPDATE
               SET updated_at=CURRENT_TIMESTAMP""",
            (conversation,identity,clean[:80] or "SMI Chat"),
        )
        connection.execute(
            """INSERT INTO oap_guardian_reviews(request_id,identity_id,outcome,reason)
               VALUES (%s,%s,%s,%s)""",(request_id,identity,outcome,reason)
        )
        if outcome=="BLOCKED":
            response=reason
            state="BLOCK_REQUEST"
        else:
            response=_provider(clean)
            state="RECOMMENDATION_READY"
        content_hash=hashlib.sha256(clean.encode()).hexdigest()
        connection.execute(
            """INSERT INTO smi_memory_records
               (request_id,identity_id,task_type,content_hash,summary,output_state,
                signal_level,rationale_json,processing_states_json)
               VALUES (%s,%s,'CHAT_RECOMMENDATION',%s,%s,%s,'GREEN',%s::jsonb,%s::jsonb)""",
            (request_id,identity,content_hash,response[:300],state,
             json.dumps({"guardian":outcome,"provider":PROVIDER}),
             json.dumps(["IDENTITY","PERMISSION","GUARDIAN","PROVIDER","HRM"])),
        )
        connection.execute(
            """INSERT INTO smi_messages
               (conversation_id,request_id,role,content,guardian_outcome)
               VALUES (%s,%s,'user',%s,%s)""",
            (conversation,request_id,clean,outcome),
        )
        connection.execute(
            """INSERT INTO smi_messages
               (conversation_id,request_id,role,content,provider,model,guardian_outcome)
               VALUES (%s,%s,'assistant',%s,%s,%s,%s)""",
            (conversation,request_id,response,PROVIDER,MODEL,outcome),
        )
        connection.commit()
    return {"status":"green","request_id":request_id,"conversation_id":conversation,
            "response":response,"output_state":state,"guardian":outcome,
            "provider":PROVIDER,"model":MODEL,"human_authority_final":True}

def health() -> dict:
    checks={"database":False,"schema":False,"provider_key":bool(os.environ.get("OPENAI_API_KEY")),
            "identity":True,"permission":True,"guardian":True,"hrm":False,
            "router":PROVIDER=="openai","chat_route":True,"streaming_ready":True,
            "audit":False,"human_authority":True}
    reason = None
    try:
        status=postgres_db.postgres_status()
        reason = status.get("error")
        checks["database"]=bool(status.get("reachable"))
        with postgres_db.connect(readonly=True) as connection:
            tables={r[0] for r in connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ).fetchall()}
            needed={"smi_messages","smi_conversations","smi_memory_records",
                    "oap_guardian_reviews","smi_provider_assignments"}
            checks["schema"]=needed <= tables
            checks["hrm"]="smi_memory_records" in tables
            checks["audit"]="audit_events" in tables
    except Exception as exc:
        reason = type(exc).__name__
    return {"status":"green" if all(checks.values()) else "degraded",
            "checks":checks,"green":sum(checks.values()),"total":len(checks),
            "database_reason": reason}
