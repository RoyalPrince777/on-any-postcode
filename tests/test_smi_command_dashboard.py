from __future__ import annotations

from mission_control import smi_command_dashboard


def test_smi_command_dashboard_composes_canonical_sources():
    command = smi_command_dashboard.status()

    assert command["component"] == "SMI Founder Command Dashboard"
    assert command["brain"]["count"] == 1
    assert command["brain"]["regions"] == 14
    assert command["brain"]["lenses"] == 28
    assert command["intelligence"]["worlds"] == 7
    assert command["intelligence"]["agents"] == 78
    assert command["bank"]["software_controls_present"] is True
    assert command["bank"]["account_engine_present"] is True
    assert command["bank"]["single_pay_gateway"] is True
    assert command["bank"]["rights_record_required"] is True
    assert command["bank"]["orchestrator_present"] is True
    assert command["bank"]["direct_authorisation_bypass_allowed"] is False
    assert command["bank"]["regulated_execution_enabled"] is False
    assert command["bank"]["operational_bank"] is False
    assert command["bank"]["licence_verified"] is False
    assert command["bank"]["money_movement"] is False
    unlock = command["bank"]["regulated_unlock"]
    assert unlock["total"] == 8
    assert unlock["unlocked_count"] >= 0
    assert set(unlock["capabilities"]) == {
        "accept_deposits",
        "bank_accounts",
        "cash_out",
        "execute_payments",
        "foreign_exchange",
        "hold_customer_funds",
        "issue_payment_cards",
        "issue_redeemable_sika",
    }
    assert command["risk_router"]["routes"] == (
        "DIRECT_ANSWER",
        "PREPARE",
        "CONFIRM",
        "GOVERNANCE",
        "BLOCK",
    )
    assert command["execution_granted"] is False
    assert command["approval_granted"] is False
    assert command["human_authority_final"] is True


def test_smi_command_dashboard_route_is_read_only(client):
    response = client.get("/mission/smi")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "SMI Command Centre" in page
    assert "SOVEREIGN MEGAVERSE INTELLIGENCE" in page
    assert "SMI central command" in page
    assert "OAP systems" in page
    assert "SYSTEM STATUS" in page
    assert "War Room" in page
    assert "Founder Final" in page
    assert "Telecom truth review" not in page
    assert ">Graphs<" not in page
    assert ">Monitors<" not in page
    assert 'method="post"' not in page.lower()
    assert client.post("/mission/smi").status_code == 405


def test_smi_command_dashboard_status_is_redacted_read_only(client):
    response = client.get("/mission/smi/status")
    payload = response.get_json()
    serialized = response.get_data(as_text=True).lower()

    assert response.status_code == 200
    assert payload["execution_granted"] is False
    assert payload["approval_granted"] is False
    assert payload["human_authority_final"] is True
    assert payload["bank"]["software_controls_present"] is True
    assert payload["bank"]["single_pay_gateway"] is True
    assert payload["bank"]["direct_authorisation_bypass_allowed"] is False
    assert payload["bank"]["regulated_execution_enabled"] is False
    assert payload["bank"]["money_movement"] is False
    for forbidden in ("password", "private_key", "signing_key", "secret", "token"):
        assert forbidden not in serialized



def test_regulated_unlock_matrix_fails_closed_when_evidence_store_unavailable(monkeypatch):
    monkeypatch.setattr(
        smi_command_dashboard.sika_execution_gate,
        "capability_matrix",
        lambda: (_ for _ in ()).throw(
            smi_command_dashboard.bank_authorisation_store.BankEvidenceUnavailable(
                "store unavailable"
            )
        ),
    )
    unlock = smi_command_dashboard._regulated_unlock_matrix()
    assert unlock["evidence_available"] is False
    assert unlock["unlocked_count"] == 0
    assert unlock["all_unlocked"] is False
    assert all(value is False for value in unlock["capabilities"].values())


def test_smi_home_has_exactly_seven_unique_doors_and_truthful_mail_scope():
    command = smi_command_dashboard.status()
    doors = command["doors"]
    assert len(doors) == 7
    assert len({door["id"] for door in doors}) == 7
    assert [door["id"] for door in doors] == [
        "smi", "command", "interaction", "control", "lab", "studio", "recovery"
    ]
    assert command["interaction"]["phone"]["built"] is True
    assert command["interaction"]["walkie_talkie"]["built"] is True
    assert command["interaction"]["messages"]["built"] is True
    assert command["interaction"]["my_line"]["built"] is True
    assert command["interaction"]["oap_mail"]["built"] is True
    assert command["interaction"]["oap_mail"]["href"] == "/mail"
    assert command["interaction"]["oap_mail"]["mailbox_read_built"] is True
    assert command["interaction"]["oap_mail"]["inbox_receive_built"] is False
    assert command["interaction"]["oap_mail"]["inbound_transport_built"] is False
    assert command["interaction"]["incoming"]["href"] == "/linkup/incoming"
    assert command["interaction"]["recents"]["href"] == "/linkup/calls/recents"
    assert command["telecom"]["validation_passed"] is True
    assert command["telecom"]["software_control_plane_ready"] is True
    assert command["telecom"]["seven_stars"]["truth"] == "PROVEN"
    assert command["telecom"]["seven_stars"]["compliance"] in {"PROVEN", "BLOCKED"}


def test_smi_home_cockpit_is_low_noise_and_route_backed():
    command = smi_command_dashboard.status()
    assert [item["id"] for item in command["cockpit"]] == [
        "brain", "graphs", "monitors", "signals", "incoming", "nexus"
    ]
    assert command["interaction"]["phone"]["href"] == "/linkup?intent=link-call"
    assert command["interaction"]["walkie_talkie"]["href"] == "/ptt"
    assert command["interaction"]["messages"]["href"] == "/linkup?intent=message"
    assert command["interaction"]["my_line"]["href"] == "/my-line"


def test_smi_essential_controls_have_clear_labels_functions_owners_and_real_routes(client):
    command = smi_command_dashboard.status()
    controls = command["sovereign_ui"]["essential_controls"]

    assert [control["id"] for control in controls] == [
        "smi_chat",
        "intelligence",
        "movement",
        "learning",
        "memory",
        "protection",
        "war_room",
        "recovery",
        "founder_final",
    ]
    assert len({control["id"] for control in controls}) == len(controls)

    expected = {
        "smi_chat": ("Talk to SMI", "/mission/ollama", "SMI"),
        "intelligence": ("Intelligence", "/mission/agents", "SMI"),
        "movement": ("Movement", "/movement", "Movement Intelligence"),
        "learning": ("Learning", "/mission/improvement", "HRM + SMI"),
        "memory": ("Memory", "/mission/organism", "HRM / JOOG"),
        "protection": ("Protection", "/mission/war-room", "Guardian"),
        "war_room": ("War Room", "/mission/war-room", "War Room"),
        "recovery": ("Recovery", "/mission/war-room", "Recovery"),
        "founder_final": ("Founder Final", "/mission/war-room", "Human Authority"),
    }

    for control in controls:
        label, href, owner = expected[control["id"]]
        assert control["label"] == label
        assert control["href"] == href
        assert control["owner"] == owner
        assert control["function"].strip()
        assert control["route_label"].strip()
        response = client.get(href)
        assert response.status_code == 200, (control["id"], href, response.status_code)


def test_smi_home_renders_clear_control_functions_and_founder_final_route(client):
    page = client.get("/mission/smi").get_data(as_text=True)

    for label in (
        "Talk to SMI",
        "Intelligence",
        "Movement",
        "Learning",
        "Memory",
        "Protection",
        "War Room",
        "Recovery",
        "Founder Final",
    ):
        assert label in page

    assert 'href="/mission/war-room"' in page
    assert 'href="/mission/organism"' in page
    assert 'href="/mission/ollama"' in page
    assert 'href="/world"' in page


def test_smi_command_dashboard_exposes_truthful_inference_readiness():
    command = smi_command_dashboard.status()
    inference = command["inference"]
    assert set(inference) == {
        "first_party_ready", "local_reachable", "local_model_available",
        "local_reason", "bridge_configured", "worker_recently_seen",
        "durable_worker_fresh", "fallback_configured", "truth",
    }
    assert inference["truth"] in {"FIRST_PARTY_READY", "FIRST_PARTY_BLOCKED"}


def test_smi_command_dashboard_front_surface_has_backend_controls(client):
    page = client.get("/mission/smi").get_data(as_text=True)
    assert "SMI inference" in page
    assert "Check evidence" in page
    assert "Talk to SMI" in page
    assert "No invented global counts" in page



def test_smi_command_dashboard_puts_important_signals_first():
    command = smi_command_dashboard.status()
    signals = command["important_signals"]
    assert len(signals) == 7
    assert signals[0]["id"] == "inference"
    assert signals[0]["label"] == "SMI Inference"
    assert signals[-1]["id"] == "human_authority"


def test_smi_slow_status_logs_only_component_and_duration(monkeypatch, caplog):
    clock = iter((10.0, 10.6))
    monkeypatch.setattr(smi_command_dashboard.time, "monotonic", lambda: next(clock))
    with caplog.at_level("WARNING", logger=smi_command_dashboard.__name__):
        result = smi_command_dashboard._timed_status(
            "inference", lambda: {"private": "must-not-log"}
        )
    assert result == {"private": "must-not-log"}
    assert "component=inference" in caplog.text
    assert "duration_ms=600.0" in caplog.text
    assert "must-not-log" not in caplog.text


def test_smi_fast_status_does_not_emit_warning(monkeypatch, caplog):
    clock = iter((10.0, 10.01))
    monkeypatch.setattr(smi_command_dashboard.time, "monotonic", lambda: next(clock))
    with caplog.at_level("WARNING", logger=smi_command_dashboard.__name__):
        assert smi_command_dashboard._timed_status("brain", lambda: True) is True
    assert "smi_dashboard_slow_component" not in caplog.text


def test_smi_home_does_not_wait_for_full_evidence_projection(client, monkeypatch):
    """The Founder landing screen must not block on War Room/regulated DB reads."""
    def fail_if_called():
        raise AssertionError("heavy evidence should not run on initial SMI page")

    monkeypatch.setattr(smi_command_dashboard, "status", fail_if_called)
    monkeypatch.setattr(
        smi_command_dashboard.war_room,
        "get_war_room_dashboard",
        fail_if_called,
    )
    monkeypatch.setattr(
        smi_command_dashboard.sika_execution_gate,
        "capability_matrix",
        fail_if_called,
    )
    response = client.get("/mission/smi")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "SMI Command Centre" in html
    assert "NOT CHECKED" in html
    assert "Check evidence" in html
    assert "setInterval(check" not in html


def test_smi_fast_shell_does_not_claim_unchecked_evidence_is_green():
    shell = smi_command_dashboard.home_shell_status()
    assert shell["evidence_state"] == "UNKNOWN"
    assert shell["war_room"]["validation_passed"] is False
    assert shell["execution_granted"] is False
    assert shell["approval_granted"] is False
    assert shell["human_authority_final"] is True
    assert len(shell["sovereign_ui"]["essential_controls"]) == 9
    assert all(
        signal["state"] == "UNKNOWN"
        for signal in shell["important_signals"]
        if signal["id"] != "human_authority"
    )


def test_single_smi_command_centre_and_chat_tool_share_existing_routes(client):
    """Only the visual home is the command centre; chat remains a separate tool."""
    home = client.get("/mission/smi")
    assert home.status_code == 200
    page = home.get_data(as_text=True)
    assert "SMI Command Centre" in page
    assert 'href="/mission/ollama"' in page
    assert "NOT CHECKED" in page
    assert 'href="/mission/smi/status"' in page
    assert "smi_command_dashboard.status()" not in page

    chat = client.get("/mission/ollama")
    assert chat.status_code == 200
    html = chat.get_data(as_text=True)
    assert 'smi-chat-tool-only' in html
    assert 'href="/mission/smi"' in html
    assert 'id="chat-form"' in html
    assert "smi_canonical_controller.js" in html


def test_smi_command_centre_prioritises_one_auto_conversation(client):
    """SMI dialogue is the primary action; specialist routes are secondary."""
    response = client.get("/mission/smi")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'class="smi-talk-primary"' in page
    assert 'href="/mission/ollama"' in page
    assert "AUTO 3 / 7 / 21" in page
    assert 'aria-label="Secondary intelligence routes"' in page
    assert 'href="/mission/war-room"' in page
    assert 'href="/mission/agents"' in page
    assert "NOT CHECKED" in page
    assert "setInterval(" not in page


def test_one_canonical_smi_dashboard_no_legacy_templates():
    """Old dashboard presentations are absent, backend functionality remains."""
    from pathlib import Path

    templates = Path(__file__).resolve().parents[1] / "mission_control" / "templates"
    assert (templates / "smi_visual_home.html").is_file()
    assert not (templates / "smi_command_dashboard.html").exists()
    assert not (templates / "smi_fast_local.html").exists()

    visual = (templates / "smi_visual_home.html").read_text(encoding="utf-8")
    for route in ("/mission/ollama", "/mission/war-room", "/mission/agents",
                  "/mission/brain", "/hrm", "/guardian", "/sika", "/oap-lab"):
        assert 'href="' + route + '"' in visual
    assert "UNKNOWN" in visual


def test_talk_to_smi_opens_existing_chat_only_on_user_action(client):
    """Sole visual home must not preload the chat iframe or add new chat routes."""
    response = client.get("/mission/smi")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.count('data-smi-talk') >= 2
    assert 'id="smi-chat-panel"' in html
    assert 'data-src="/mission/ollama"' in html
    import re

    assert not re.search(r'(?<![\w-])src="/mission/ollama"', html)
    assert "if (!frame.hasAttribute('src'))" in html
    assert "frame.removeAttribute('src')" in html
    assert 'href="/mission/war-room"' in html
    assert "setInterval(" not in html


def test_smi_mobile_home_keeps_dynamic_controls_but_collapses_route_noise():
    """The first phone view is Talk to SMI; existing protected routes remain reachable."""
    from pathlib import Path

    template = (Path(__file__).resolve().parents[1] / "mission_control" /
                "templates" / "smi_visual_home.html").read_text(encoding="utf-8")
    assert '<details class="smi-route-drawer" open>' in template
    assert 'aria-label="OAP systems"' in template
    assert "window.matchMedia('(max-width: 760px)').matches" in template
    assert 'routes.open = false;' in template
    assert 'intelligence.open = false;' in template
    assert 'summary:focus-visible' in template
    assert '.intel-panel{display:none}' in template
    assert '.right-details>summary{display:flex' in template
    assert 'class="smi-talk-primary"' in template
    for required in ('/my-world', '/mission/ollama', '/guardian', '/hrm',
                     '/mission/war-room', '/mission/smi/status', '/arena'):
        assert required in template
    assert 'UNKNOWN' in template and 'NOT CHECKED' in template
    assert "frame.removeAttribute('src')" in template


def test_smi_cc_linkup_ci_receipt_does_not_promote_release_green(client):
    """A dated 7/7 source receipt must never turn the global Green Gate green."""
    from pathlib import Path

    page = client.get("/mission/smi")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert 'aria-label="Link Up verified source receipt"' in html
    assert "7/7 passed" in html
    assert "Source snapshot · 20 Nov 2026" in html
    assert "17eac4f" in html
    assert "5,659 tests passed, 9 skipped, 1 warning" in html
    assert "source, route, access-boundary and desktop/mobile-emulated Chromium" in html
    assert "LOCKED — draft, unmerged and undeployed" in html
    assert "Redmi A5, two-device messages/calls" in html
    assert "does not auto-refresh or promote the global Green Gate" in html
    assert '<div class="status"><span>Green Gate</span><b class="unknown">NOT CHECKED</b></div>' in html
    assert 'href="https://github.com/RoyalPrince777/on-any-postcode/pull/1234"' in html
    assert "setInterval(" not in html

    source = (Path(__file__).resolve().parents[1] / "mission_control" /
              "templates" / "smi_visual_home.html").read_text(encoding="utf-8")
    assert source.count('class="ci-receipt"') == 1
    assert "Founder Final" in source


def test_smi_cc_receipt_links_to_canonical_blueprint_and_keeps_release_locked():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    template = (root / "mission_control/templates/smi_visual_home.html").read_text(
        encoding="utf-8"
    )
    blueprint = (root / "docs/OAP_FULL_MASTER_BLUEPRINT_DASHBOARD_CHAT.md").read_text(
        encoding="utf-8"
    )

    assert template.count(">Full master blueprint</a>") == 1
    assert "docs/OAP_FULL_MASTER_BLUEPRINT_DASHBOARD_CHAT.md" in template
    assert blueprint.count("## 26. Verified SMI CC, Link Up") == 1
    assert "SOURCE CI GREEN, RELEASE LOCKED" in blueprint
    assert "same_revision_on_physical_redmi_a5" in blueprint
    assert "two_real_phones_deliver_and_reconnect_with_receipts" in blueprint
    assert "authority_green" in blueprint
    assert "No CI percentage, button or static receipt may self-approve" in blueprint


def test_master_upgrade_section_29_canonical_routes_and_release_lock():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    blueprint = (root / "docs/OAP_FULL_MASTER_BLUEPRINT_DASHBOARD_CHAT.md").read_text(encoding="utf-8")
    template = (root / "mission_control/templates/smi_visual_home.html").read_text(encoding="utf-8")

    assert blueprint.count("## 29. Full master upgrade") == 1
    assert "KORADASO Internet       /koradaso" in blueprint
    assert "My World                /my-world" in blueprint
    assert "SMI Command Centre      /mission/smi" in blueprint
    assert "static/oap-browse-apps.css" in blueprint
    assert "separate" in blueprint and "not been" in blueprint
    assert "b0f7b745cd5fe38aa03f2b1ea8a925aaff8ccb0a" in blueprint
    assert "17eac4f289a0d5118d0dd5639a99d27e1f65bb3b" in blueprint
    assert "source_green" in blueprint and "release_green" in blueprint
    assert "UNTESTED / UNKNOWN / STALE / FAILED => LOCKED" in blueprint
    assert "No additional dashboard, release permission" in blueprint
    assert template.count('class="ci-receipt"') == 1
    assert "KORADASO · dated source proof" in template
    assert "KORADASO PR" in template
    assert '<span>Green Gate</span><b class="unknown">NOT CHECKED</b>' in template
