"""Governed SMI Chat runtime: identity, permission, Guardian, provider and HRM."""
from __future__ import annotations
import hashlib, json, os, re, uuid
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from . import live_brain, postgres_db

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

def _provider(message: str, image_data: str = "", history: list[dict[str, str]] | None = None, brain: dict | None = None) -> str:
    key=os.environ.get("OPENAI_API_KEY","").strip()
    if not key:
        raise RuntimeError("provider_key_missing")
    system=(
        "You are SMI: Sovereign Megaverse Intelligence, the governed intelligence brain "
        "inside the ON ANY POSTCODE (OAP) Digital Organism. Never call yourself a generic AI. "
        "Use OAP language and preserve continuity from the supplied conversation. Lead with a "
        "direct, practical answer; infer obvious intent and ask a question only when missing "
        "information materially changes the answer. Do not offer repetitive multiple-choice "
        "clarifications. OAP means ON ANY POSTCODE. Follow the governance law: Intelligence "
        "proposes, Guardian protects, Builder creates, Identity validates, Sovereign decides, "
        "HRM remembers, Organism grows. You provide recommendations only, never claim final "
        "authority and never execute actions. Human Authority remains final. Be concise but "
        "complete, and end with the clearest useful next action when appropriate. "
        "Use the canonical brain routing context below as governed routing metadata, not as "
        "private chain-of-thought. " + json.dumps({
            "task_type": (brain or {}).get("task_type"),
            "approved_advisors": (brain or {}).get("advisor_ids", []),
            "signal_level": (brain or {}).get("signal_level"),
            "war_room_triggered": (brain or {}).get("war_room", {}).get("triggered", False),
        }, separators=(",", ":"))
    )
    user_content=[{"type":"input_text","text":message or "Describe and analyse the attached image."}]
    if image_data:
        user_content.append({"type":"input_image","image_url":image_data})
    inputs=[{"role":"system","content":[{"type":"input_text","text":system}]}]
    for item in (history or [])[-12:]:
        role=item.get("role")
        content=_clean(item.get("content"),4000)
        if role in {"user","assistant"} and content:
            inputs.append({"role":role,"content":[{"type":"input_text","text":content}]})
    inputs.append({"role":"user","content":user_content})
    payload=json.dumps({
        "model":MODEL, "input":inputs, "max_output_tokens":900,
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

def chat(message: object, identity_id: str, display_name: object, conversation_id: object=None, image_data: object=None) -> dict:
    clean=_clean(message,MAX_INPUT)
    image=_clean(image_data,7_000_000)
    if image and not re.match(r"^data:image/(?:png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$", image):
        raise ValueError("invalid_image")
    if len(image) > 7_000_000:
        raise ValueError("image_too_large")
    if not clean and image:
        clean="Describe and analyse this image."
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
        owner=connection.execute(
            "SELECT identity_id FROM smi_conversations WHERE conversation_id=%s",
            (conversation,),
        ).fetchone()
        if owner and str(owner[0]) != identity:
            conversation=str(uuid.uuid4())
        connection.execute(
            """INSERT INTO smi_conversations(conversation_id,identity_id,title)
               VALUES (%s,%s,%s) ON CONFLICT (conversation_id) DO UPDATE
               SET updated_at=CURRENT_TIMESTAMP""",
            (conversation,identity,clean[:80] or "SMI Chat"),
        )
        rows=connection.execute(
            """SELECT m.role,m.content FROM smi_messages m
               JOIN smi_conversations c ON c.conversation_id=m.conversation_id
               WHERE m.conversation_id=%s AND c.identity_id=%s
               ORDER BY m.created_at DESC LIMIT 12""",
            (conversation,identity),
        ).fetchall()
        history=[{"role":str(row[0]),"content":str(row[1])} for row in reversed(rows)]
        brain=live_brain.review(
            request_id=request_id, identity_id=identity, content=clean,
            history=history, image_attached=bool(image),
        )
        if not brain["passed"]:
            outcome="BLOCKED"
            reason=brain["guardian_reason"] or "Canonical Guardian blocked the request."
        elif outcome=="PASSED":
            reason=brain["guardian_reason"] or "Canonical SMI review passed."
        connection.execute(
            """INSERT INTO oap_guardian_reviews(request_id,identity_id,outcome,reason)
               VALUES (%s,%s,%s,%s)""",(request_id,identity,outcome,reason)
        )
        if outcome=="BLOCKED":
            response=reason
            state="BLOCK_REQUEST"
        else:
            response=_provider(clean,image,history,brain)
            state=brain["output_state"]
        content_hash=hashlib.sha256((clean + ("|image" if image else "")).encode()).hexdigest()
        connection.execute(
            """INSERT INTO smi_memory_records
               (request_id,identity_id,task_type,content_hash,summary,output_state,
                signal_level,rationale_json,processing_states_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)""",
            (request_id,identity,brain["task_type"],content_hash,response[:300],state,
             brain["signal_level"],
             json.dumps({"guardian":outcome,"provider":PROVIDER,"image_attached":bool(image),
                         "advisor_ids":brain["advisor_ids"],"war_room":brain["war_room"]}),
             json.dumps(brain["processing_states"]+["PROVIDER_COMPLETED","HRM_RECORDED"])),
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
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
        previous = connection.execute(
            "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
        ).fetchone()
        prev_hash = str(previous[0]) if previous else "GENESIS"
        audit_payload = json.dumps({
            "request_id": request_id, "identity_id": identity,
            "action": "SMI_REVIEWED", "guardian": outcome,
            "provider": PROVIDER, "model": MODEL, "image_attached": bool(image),
            "task_type": brain["task_type"], "advisor_ids": brain["advisor_ids"],
            "brain_regions": brain["brain_region_count"], "war_room": brain["war_room"]["triggered"],
        }, sort_keys=True, separators=(",", ":"))
        curr_hash = hashlib.sha256((prev_hash + audit_payload).encode()).hexdigest()
        connection.execute(
            """INSERT INTO audit_events
               (prev_hash,curr_hash,actor_id,actor_type,authority_level,
                action,target,reason,correlation_id,metadata)
               VALUES (%s,%s,%s,'HUMAN',5,'SMI_REVIEWED','SMI_CHAT',%s,%s,%s::jsonb)""",
            (prev_hash,curr_hash,identity,reason,request_id,audit_payload),
        )
        connection.commit()
    return {"status":"green","request_id":request_id,"conversation_id":conversation,
            "response":response,"output_state":state,"guardian":outcome,
            "provider":PROVIDER,"model":MODEL,"human_authority_final":True,
            "task_type":brain["task_type"],"advisor_ids":brain["advisor_ids"],
            "brain_regions":brain["brain_region_count"],"signal_level":brain["signal_level"],
            "war_room":brain["war_room"],"can_execute":False}

def health() -> dict:
    """Return the truthful OAP 3x7 (21-gate) SMI production readiness result."""
    checks={
        "database":False, "schema":False,
        "provider_key":bool(os.environ.get("OPENAI_API_KEY")),
        "provider_assignment":False, "identity":True, "permission":True,
        "nexus":False, "thalamus_input":False, "agent_registry":False,
        "agent_selection":False, "biological_brain":False, "aegis":False,
        "guardian":False, "war_room":False, "hrm":False,
        "conversation_memory":False, "router":PROVIDER=="openai",
        "chat_route":True, "audit":False, "human_authority":True,
        "execution_locked":True,
    }
    reason = None
    try:
        probe=live_brain.review(
            request_id=str(uuid.uuid4()), identity_id=str(uuid.uuid4()),
            content="SMI health readiness review", history=[], image_attached=False,
        )
        checks["nexus"]=True
        checks["thalamus_input"]=True
        checks["agent_registry"]=probe["agent_count"] >= 1
        checks["agent_selection"]=probe["agent_count"] >= 1
        checks["biological_brain"]=probe["brain_region_count"] >= 12
        checks["aegis"]=bool(probe["safety_codes"])
        checks["guardian"]=bool(probe["passed"])
        checks["war_room"]="war_room" in probe
        checks["execution_locked"]=probe["can_execute"] is False
    except Exception as exc:
        reason="canonical_brain_"+type(exc).__name__
    try:
        status=postgres_db.postgres_status()
        reason = reason or status.get("error")
        checks["database"]=bool(status.get("reachable"))
        with postgres_db.connect(readonly=True) as connection:
            tables={r[0] for r in connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ).fetchall()}
            needed={"smi_messages","smi_conversations","smi_memory_records",
                    "oap_guardian_reviews","smi_provider_assignments"}
            checks["schema"]=needed <= tables
            checks["hrm"]="smi_memory_records" in tables
            checks["conversation_memory"]={"smi_messages","smi_conversations"} <= tables
            checks["audit"]="audit_events" in tables
            checks["provider_assignment"]=connection.execute(
                """SELECT 1 FROM smi_provider_assignments
                   WHERE agent_id='NEO-001' AND provider_id='openai'
                     AND status='APPROVED' LIMIT 1"""
            ).fetchone() is not None
    except Exception as exc:
        message = str(exc)
        if message in {"DATABASE_URL is not configured", "Neon database URL is not configured",
                       "psycopg is required when DATABASE_URL is configured"}:
            reason = message
        else:
            reason = reason or type(exc).__name__
    return {"status":"green" if all(checks.values()) else "degraded",
            "checks":checks,"green":sum(checks.values()),"total":len(checks),
            "database_reason": reason,
            "constitution":{"protocol":"3x7","human_authority_final":True,
                            "independent_execution":False},
            "environment": {
                "revision_present": bool(os.environ.get("OAP_ENV_REVISION")),
                "database_url_present": bool(os.environ.get("DATABASE_URL")),
                "oap_neon_url_present": bool(os.environ.get("OAP_NEON_DATABASE_URL")),
                "db_secret_present": bool(os.environ.get("OAP_DB_SECRET_B64") or
                                          os.environ.get("OAP_NEON_DATABASE_URL_B64")),
            }}
