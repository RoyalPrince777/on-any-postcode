"""
OAP Sovereign Mission Control Gateway
Read-only, production-grade operations hub.
Preserves Flask + SQLite + Termux/Android local-first architecture.
"""
import os
from flask import Blueprint

# Mission Control Blueprint (read-only routes only)
mc_bp = Blueprint(
    "mission_control",
    __name__,
    url_prefix="/mission",
    template_folder="templates",
    static_folder="static",
    static_url_path="/mission/static",
)

# Register read-only routes
from . import views

mc_bp.add_url_rule("/", "index", views.mission_index)
mc_bp.add_url_rule("", "slash", views.mission_index)
mc_bp.add_url_rule("/status", "status", views.mission_status)


def init_app(app):
    """
    Initialize Mission Control for Flask application.
    Fails safely if module is incomplete.
    
    Args:
        app: Flask application instance
    
    Raises:
        Exception: If registration fails (caller must handle gracefully)
    """
    app.register_blueprint(mc_bp)
    
    # Register CLI commands
    @app.cli.command("mission-status")
    def mission_status_cmd():
        """Show Mission Control status (read-only)."""
        from . import status as mc_status
        s = mc_status.get_public_gateway_status()
        print(f"Local Mode: {s.get('local_mode')}")
        print(f"Database: {s.get('database')}")
        print(f"HRM Audit Chain: {s.get('audit_chain')}")
        print(f"Guardian: {s.get('guardian')}")
        print(f"Ollama: {s.get('ollama')}")
        print(f"Approval Queue: {s.get('approval_queue')}")
