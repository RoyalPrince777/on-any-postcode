import json
import logging
import os
import sys
import time
import uuid
from urllib import parse as urlparse

from flask import (
    Flask,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from mission_control import (
    approval_service,
    authority,
    carnival_intelligence,
    founder_activation,
    judgement,
    languages,
    link_relationships,
    linkup,
    location_intelligence,
    neon_auth,
    product_store,
    products,
    public_store,
    smi_chat_runtime,
    telemetry,
    web_security,
    workspaces,
)
from mission_control import init_app as _mc_init
from mission_control.agents import validate_agent_registry
from mission_control.database import db_status
from mission_control.organism import validate_architecture

app = Flask(__name__)
REQUEST_LOGGER = logging.getLogger("oap.request")
if not REQUEST_LOGGER.handlers:
    request_log_handler = logging.StreamHandler(sys.stdout)
    request_log_handler.setFormatter(logging.Formatter("%(message)s"))
    REQUEST_LOGGER.addHandler(request_log_handler)
REQUEST_LOGGER.setLevel(logging.INFO)
REQUEST_LOGGER.propagate = False
SESSION_SECRET_CONFIGURED = bool(os.environ.get("OAP_SESSION_SECRET", "").strip())
app.config["SECRET_KEY"] = (
    os.environ.get("OAP_SESSION_SECRET", "").strip() or os.urandom(32)
)
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("OAP_LOCAL_MODE", "false").lower() != "true"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

MAX_PUBLIC_RECORDS = 100
FOUNDER_ONLY_PATH_PREFIXES = (
    "/api/infrastructure",
    "/infrastructure",
    "/mission",
    "/my-world",
    "/myworld",
)
CARNIVAL_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
    "form-action 'self'; object-src 'none'; img-src 'self' data:; "
    "media-src 'self'; connect-src 'self'; style-src 'self'; "
    "script-src 'self'; frame-src https://www.openstreetmap.org"
)
FOUNDER_ACTIVATED_SESSION_KEY = "oap_founder_activation_completed"

# NOTE: file replacement intentionally aborted below if content is incomplete.
