"""Durable PostgreSQL persistence for EARTH IS OUR TURF M Town."""
from __future__ import annotations

import hashlib
import json
import secrets
from typing import Any

from mission_control import postgres_db

SCHEMA_STATEMENTS=(
"""CREATE TABLE IF NOT EXISTS oap_eiot_world_saves(
 save_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 world_id UUID NOT NULL,
 player_ref TEXT NOT NULL,
 reconnect_token_hash TEXT NOT NULL UNIQUE,
 revision BIGINT NOT NULL DEFAULT 1,
 world_state JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(world_id,player_ref))""",
"""CREATE INDEX IF NOT EXISTS ix_oap_eiot_world_saves_player_updated
 ON oap_eiot_world_saves(player_ref,updated_at DESC)""",
)

def _hash(token:str)->str:
    return hashlib.sha256(token.encode()).hexdigest()

def ensure_schema() -> None:
    with postgres_db.connect() as c:
        for s in SCHEMA_STATEMENTS:c.execute(s)
        c.commit()

def create_save(*,player_ref:object,state:dict[str,Any])->dict[str,Any]:
    player=str(player_ref or "").strip()
    if not player: raise ValueError("eiot_player_ref_required")
    token=secrets.token_urlsafe(32)
    payload=json.dumps(state,separators=(",",":"),sort_keys=True)
    with postgres_db.connect() as c:
        row=c.execute("""INSERT INTO oap_eiot_world_saves(world_id,player_ref,reconnect_token_hash,world_state)
        VALUES (%s,%s,%s,%s::jsonb)
        ON CONFLICT(world_id,player_ref) DO UPDATE SET world_state=EXCLUDED.world_state,
        revision=oap_eiot_world_saves.revision+1,updated_at=CURRENT_TIMESTAMP
        RETURNING save_id,world_id,revision""",(state["world_id"],player,_hash(token),payload)).fetchone()
        c.commit()
    return {"save_id":str(row[0]),"world_id":str(row[1]),"revision":int(row[2]),"reconnect_token":token}

def load_by_token(*,token:object)->dict[str,Any]:
    value=str(token or "").strip()
    if not value: raise ValueError("eiot_reconnect_token_required")
    with postgres_db.connect(readonly=True) as c:
        row=c.execute("""SELECT save_id,world_id,player_ref,revision,world_state
        FROM oap_eiot_world_saves WHERE reconnect_token_hash=%s""",(_hash(value),)).fetchone()
    if row is None: raise ValueError("eiot_reconnect_not_found")
    return {"save_id":str(row[0]),"world_id":str(row[1]),"player_ref":str(row[2]),"revision":int(row[3]),"world_state":row[4]}

def save_existing(*,token:object,state:dict[str,Any],expected_revision:object)->dict[str,Any]:
    value=str(token or "").strip()
    revision=int(expected_revision)
    payload=json.dumps(state,separators=(",",":"),sort_keys=True)
    with postgres_db.connect() as c:
        row=c.execute("""UPDATE oap_eiot_world_saves SET world_state=%s::jsonb,revision=revision+1,
        updated_at=CURRENT_TIMESTAMP WHERE reconnect_token_hash=%s AND revision=%s
        RETURNING save_id,revision""",(payload,_hash(value),revision)).fetchone()
        if row is None:
            c.rollback(); raise ValueError("eiot_save_revision_conflict")
        c.commit()
    return {"save_id":str(row[0]),"revision":int(row[1])}

def status()->dict[str,Any]:
    return {"backend":"postgresql","durable":True,"reconnect_tokens_hashed":True,"optimistic_revision":True}
