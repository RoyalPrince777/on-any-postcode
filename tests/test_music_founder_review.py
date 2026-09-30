"""Founder approval is a separate, private decision across Music and Radio."""
import inspect

from flask import Flask, render_template

from mission_control import music_content_links, music_public_views, product_core_services


def test_creator_studio_has_submission_not_founder_approval():
    app=Flask(__name__,template_folder="../mission_control/templates")
    with app.app_context():
        creator=render_template("oap_music_studio.html")
        founder=render_template("oap_music_founder_control.html")
    assert 'id="review-form"' in creator
    assert 'id="approve-form"' not in creator
    assert "Approve release" not in creator
    assert "/mission/organs/tune/review-queue" in founder
    assert "Await verified rights" in founder
    assert "/approve','POST'" in founder
    assert "not published or broadcast" in founder


def test_founder_review_routes_are_founder_only():
    app=Flask(__name__)
    app.register_blueprint(music_public_views.bp)
    assert any(rule.rule=="/music/control" for rule in app.url_map.iter_rules())
    assert "founder_only=True" in inspect.getsource(music_public_views.founder_music_control)


def test_founder_review_queue_sql_is_review_only_and_displays_actual_rights(monkeypatch):
    statements=[]
    class Result:
        def fetchall(self):
            return []
    class Connection:
        def __enter__(self):return self
        def __exit__(self,*_args):return False
        def execute(self,sql,params=()):
            statements.append((sql,params))
            return Result()
    monkeypatch.setattr(product_core_services.postgres_db,"connect",lambda **_kw:Connection())
    data=product_core_services.founder_music_review_queue()
    assert data["review_required"]==[]
    assert data["approval_does_not_publish"] is True
    assert "r.state='REVIEW_REQUIRED'" in statements[0][0]
    assert "r.rights_status" in statements[0][0]


def test_tv_video_link_is_never_publication_approval():
    source=inspect.getsource(music_content_links.add_video_link)
    assert '"tv_publication_approved": False' in source
    assert '"tv_broadcast_started": False' in source
    assert '"founder_tv_approval_required": True' in source
