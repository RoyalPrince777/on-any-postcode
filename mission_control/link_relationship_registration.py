"""Registration helper kept separate from app.py for bounded Link changes."""
from __future__ import annotations


def register(app) -> None:
    from .link_relationship_routes import bp
    app.register_blueprint(bp)
