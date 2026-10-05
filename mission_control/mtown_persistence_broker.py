"""First-party EIOT persistence broker client."""
from __future__ import annotations

import json
import os
from urllib import request as urlrequest
from typing import Any

def configured() -> bool:
    return bool(os.environ.get("OAP_EIOT_PERSISTENCE_URL","").strip() and os.environ.get("OAP_EIOT_SERVICE_KEY","").strip())

def _post(path:str,payload:dict[str,Any]) -> dict[str,Any]:
    base=os.environ.get("OAP_EIOT_PERSISTENCE_URL","").strip().rstrip("/")
    key=os.environ.get("OAP_EIOT_SERVICE_KEY","").strip()
    if not base or not key:
        raise RuntimeError("eiot_persistence_broker_unconfigured")
    body=json.dumps(payload,separators=(",",":")).encode()
    req=urlrequest.Request(
        base+path,
        data=body,
        method="POST",
        headers={"Content-Type":"application/json","X-EIOT-Service-Key":key},
    )
    try:
        with urlrequest.urlopen(req,timeout=15) as response:
            data=json.loads(response.read().decode())
    except Exception as exc:
        raise RuntimeError("eiot_persistence_broker_unavailable") from exc
    if not isinstance(data,dict):
        raise TypeError("eiot_persistence_broker_invalid")
    if data.get("error"):
        raise RuntimeError(str(data["error"]))
    return data

def initialize() -> dict[str,Any]:
    return _post("/internal/eiot/persistence/init",{})

def save(*,player_ref:object,state:dict[str,Any]) -> dict[str,Any]:
    return _post("/internal/eiot/persistence/save",{"player_ref":str(player_ref or ""),"state":state})

def reconnect(*,token:object) -> dict[str,Any]:
    return _post("/internal/eiot/persistence/reconnect",{"reconnect_token":str(token or "")})

def status() -> dict[str,Any]:
    return {"backend":"oap-core-postgresql-broker","configured":configured()}
