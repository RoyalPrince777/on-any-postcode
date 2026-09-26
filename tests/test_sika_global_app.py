from decimal import Decimal

import pytest

from mission_control import sika_global
from sika_global_app import app


def test_anchor_is_one_sika_to_one_gbp():
    quote = sika_global.quote_from_sika("25", "GBP", gbp_per_unit={})
    assert quote.local_amount == Decimal("25.00")
    assert quote.executable is False


def test_arbitrary_three_letter_currency_works_with_treasury_rate():
    quote = sika_global.quote_from_sika("10", "XYZ", gbp_per_unit={"XYZ": "0.50"})
    assert quote.local_amount == Decimal("20.00")


def test_missing_rate_fails_closed():
    with pytest.raises(sika_global.CurrencyError, match="treasury_rate_unavailable"):
        sika_global.quote_from_sika("1", "USD", gbp_per_unit={})


def test_regulated_actions_are_blocked():
    client = app.test_client()
    for path in ("/api/sika/pay", "/api/sika/card", "/api/sika/cash-out"):
        response = client.post(path)
        assert response.status_code == 423
        assert response.get_json()["money_moved"] is False


def test_app_surface_and_quote_endpoint():
    client = app.test_client()
    assert client.get("/sika").status_code == 200
    response = client.post("/api/sika/quote", json={
        "amount_sika": "100",
        "currency": "USD",
        "gbp_per_unit": {"USD": "0.80"},
    })
    assert response.status_code == 200
    assert response.get_json()["local_amount"] == "125.00"


def test_wallet_reference_ledger_is_owner_scoped_and_non_executable():
    client = app.test_client()
    created = client.post("/api/sika/ledger/reference", json={
        "owner_id": "owner-a",
        "kind": "credit_reference",
        "amount_sika": "12.50",
        "memo": "software reference only",
    })
    assert created.status_code == 201
    assert created.get_json()["money_moved"] is False
    wallet_a = client.get("/api/sika/wallet?owner_id=owner-a").get_json()
    wallet_b = client.get("/api/sika/wallet?owner_id=owner-b").get_json()
    assert wallet_a["balance_reference"] == "12.50"
    assert wallet_b["balance_reference"] == "0.00"
    assert wallet_a["executable"] is False


def test_treasury_rate_snapshot_can_feed_quote_without_external_provider():
    client = app.test_client()
    saved = client.post("/api/sika/treasury/rates", json={
        "currency": "EUR",
        "gbp_per_unit": "0.85",
        "source": "founder-approved-test-snapshot",
    })
    assert saved.status_code == 201
    response = client.post("/api/sika/quote", json={
        "amount_sika": "85",
        "currency": "EUR",
    })
    assert response.status_code == 200
    body = response.get_json()
    assert body["local_amount"] == "100.00"
    assert body["executable"] is False


def test_treasury_rate_requires_source_and_positive_value():
    client = app.test_client()
    assert client.post("/api/sika/treasury/rates", json={
        "currency": "USD",
        "gbp_per_unit": "0",
        "source": "test",
    }).status_code == 400
    assert client.post("/api/sika/treasury/rates", json={
        "currency": "USD",
        "gbp_per_unit": "0.75",
        "source": "",
    }).status_code == 400


def test_cashback_requires_funded_pool_for_funded_flag():
    client = app.test_client()
    response = client.post("/api/sika/cashback/quote", json={
        "purchase_sika": "100",
        "rate_percent": "5",
        "funded_pool_available_sika": "4",
    })
    body = response.get_json()
    assert response.status_code == 200
    assert body["reward_sika"] == "5.00"
    assert body["funded"] is False
    assert body["executable"] is False


def test_deferred_preview_builds_schedule_without_credit():
    client = app.test_client()
    response = client.post("/api/sika/deferred/preview", json={
        "purchase_sika": "120",
        "instalments": 3,
        "monthly_disposable_sika": "60",
    })
    body = response.get_json()
    assert response.status_code == 200
    assert [x["amount_sika"] for x in body["schedule"]] == ["40.00", "40.00", "40.00"]
    assert body["credit_agreement_created"] is False
    assert body["affordability_signal"] == "within_input_limit"


def test_trust_preview_is_explainable_and_not_credit_decision():
    client = app.test_client()
    response = client.post("/api/sika/trust/preview", json={
        "payment_reliability": 80,
        "cashflow_resilience": 70,
        "account_stability": 90,
        "identity_confidence": 100,
    })
    body = response.get_json()
    assert response.status_code == 200
    assert 0 <= body["score"] <= 1000
    assert len(body["why"]) == 4
    assert body["credit_decision"] is False


def test_security_freeze_fails_closed_without_live_rails():
    client = app.test_client()
    response = client.post("/api/sika/security/freeze")
    body = response.get_json()
    assert response.status_code == 423
    assert body["card_frozen"] is False
    assert body["payments_frozen"] is False
    assert body["executable"] is False


def test_visible_control_targets_have_working_endpoints():
    client = app.test_client()
    assert client.get("/api/sika/wallet").status_code == 200
    assert client.post("/api/sika/treasury/rates", json={
        "currency": "USD",
        "gbp_per_unit": "0.75",
        "source": "ui-test",
    }).status_code == 201
    for path in ("/api/sika/card", "/api/sika/pay"):
        response = client.post(path)
        assert response.status_code == 423
        assert response.get_json()["reason"] == "regulated_execution_not_enabled"


def test_surface_contains_real_buttons_not_static_tiles():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    for control_id in (
        "walletRefresh",
        "treasurySave",
        "quote",
        "cashbackBtn",
        "deferredBtn",
        "trustBtn",
        "freezeBtn",
        "marketHandoff",
    ):
        assert f'id="{control_id}"' in html
    assert 'class="tile jump"' in html
    assert 'class="tile regulated"' in html


def test_alignment_and_bank_intelligence_are_read_only():
    client = app.test_client()
    alignment = client.get("/api/sika/intelligence/alignment")
    bank = client.get("/api/sika/intelligence/bank")
    assert alignment.status_code == 200
    assert bank.status_code == 200
    a = alignment.get_json()
    b = bank.get_json()
    assert a["read_only"] is True
    assert a["executable"] is False
    assert a["sika_focus"]["one_sika"] is True
    assert b["read_only"] is True
    assert b["executable"] is False
    assert b["operational_bank"] is False
    assert b["payment_execution_enabled"] is False


def test_surface_has_alignment_and_bank_intelligence_buttons():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'data-intel="alignment"' in html
    assert 'data-intel="bank"' in html
    assert 'id="intelligenceSection"' in html


def test_fraud_preflight_is_non_executing_and_escalates():
    client = app.test_client()
    low = client.post("/api/sika/fraud/preflight", json={
        "amount_sika": "50",
        "recent_attempts": 1,
        "transactions_10m": 1,
    }).get_json()
    assert low["decision"] == "allow_software_only"
    assert low["money_moved"] is False
    high = client.post("/api/sika/fraud/preflight", json={
        "amount_sika": "1500",
        "recent_attempts": 6,
        "transactions_10m": 7,
        "new_device": True,
        "unusual_location": True,
    }).get_json()
    assert high["decision"] == "review"
    assert high["risk_score"] >= 60
    assert high["regulated_execution_authorised"] is False


def test_install_readiness_truth_boundary():
    client = app.test_client()
    response = client.get("/api/sika/install/readiness")
    body = response.get_json()
    assert response.status_code == 200
    assert body["private_software_acceptance_ready"] is True
    assert body["public_pwa_software_ready"] is True
    assert body["real_android_pwa_acceptance"] is False
    assert body["safe_public_install_ready"] is False
    assert body["sika_specific_signed_android_package"] is False
    assert body["real_native_android_install_acceptance"] is False


def test_surface_has_fraud_and_install_buttons():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="fraudBtn"' in html
    assert 'id="installReadinessBtn"' in html
    assert 'id="fraudSection"' in html
    assert 'id="installSection"' in html


def test_standalone_sika_serves_install_shell_assets():
    client = app.test_client()
    manifest = client.get("/manifest.webmanifest")
    worker = client.get("/service-worker.js")
    controller = client.get("/assets/oap-os.js")
    icon = client.get("/assets/oap-os-icon-192.png")
    offline = client.get("/offline")

    assert manifest.status_code == 200
    assert manifest.content_type == "application/manifest+json"
    assert worker.status_code == 200
    assert worker.headers["Service-Worker-Allowed"] == "/"
    assert controller.status_code == 200
    assert icon.status_code == 200
    assert icon.data.startswith(b"\x89PNG\r\n\x1a\n")
    assert offline.status_code == 200


def test_sika_page_exposes_install_controller():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'rel="manifest" href="/manifest.webmanifest"' in html
    assert 'data-oap-install hidden' in html
    assert 'src="/assets/oap-os.js"' in html


def test_payment_licence_gate_stays_closed_without_verified_evidence():
    client = app.test_client()
    response = client.get("/api/sika/payment-licence")
    body = response.get_json()
    assert response.status_code == 200
    assert body["licence_evidence_complete"] is False
    assert body["payment_adapter_may_enter_release_review"] is False
    assert body["payment_execution_enabled"] is False
    assert body["customer_funds_enabled"] is False


def test_surface_has_payment_licence_gate_button():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="licenceBtn"' in html
    assert 'id="licenceSection"' in html


def test_sika_app_hierarchy_is_aligned_without_removing_working_controls():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)

    assert "Money & Value" in html
    assert "Protection & Intelligence" in html
    assert "Advanced / Control Center" in html
    assert 'aria-label="SIKA truth status"' in html

    for control in (
        "walletRefresh",
        "quote",
        "treasurySave",
        "cashbackBtn",
        "deferredBtn",
        "trustBtn",
        "freezeBtn",
        "fraudBtn",
        "installReadinessBtn",
        "licenceBtn",
        "marketHandoff",
    ):
        assert f'id="{control}"' in html

    assert "PWA software readiness is separate from physical Android acceptance" in html
    assert "Customer funds, bank accounts, card issuance, cash-out and payment execution remain licence-gated" in html


def test_install_readout_uses_current_readiness_contract():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert "j.public_pwa_software_ready" in html
    assert "j.real_android_pwa_acceptance" in html
    assert "j.native_android_package_ready" in html


def test_a5_preparation_pack_is_complete_but_non_executing():
    client = app.test_client()
    response = client.get("/api/sika/a5-preparation")
    body = response.get_json()
    assert response.status_code == 200
    assert all(body["preparation_actions"].values())
    assert body["preparation_only"] is True
    assert body["a6_execution_granted"] is False
    assert body["a7_enabled"] is False
    assert body["payment_execution_enabled"] is False


def test_surface_has_a5_preparation_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="a5Btn"' in html
    assert 'id="a5Section"' in html


def test_a6_readiness_reuses_canonical_gate_and_never_self_grants_execution():
    client = app.test_client()
    response = client.get("/api/sika/a6-readiness")
    body = response.get_json()
    assert response.status_code == 200
    assert body["level"] == "A6"
    assert body["execution_granted"] is False
    assert body["payment_execution_enabled"] is False
    assert body["a7_enabled"] is False
    assert body["self_permission_change_allowed"] is False
    assert body["human_authority_final"] is True


def test_surface_has_a6_readiness_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="a6Btn"' in html
    assert 'id="a6Section"' in html


def test_a6_evidence_pack_runs_real_fail_closed_policy_without_execution():
    client = app.test_client()
    response = client.get("/api/sika/a6-evidence-pack")
    body = response.get_json()
    assert response.status_code == 200
    proof = body["software_fail_closed_precheck"]
    assert proof["proof_class"] == "software_policy_execution"
    assert proof["allowed"] is False
    assert proof["execution_granted"] is False
    assert body["production_state_mutated"] is False
    assert body["payment_execution_enabled"] is False


def test_surface_has_a6_fail_closed_proof_button():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="a6EvidenceBtn"' in html


def test_open_banking_trial_is_read_only_and_non_monetary():
    client = app.test_client()
    status = client.get("/api/sika/open-banking/status").get_json()
    trial = client.get("/api/sika/open-banking/trial").get_json()
    assert status["read_only_account_information"] is True
    assert status["payment_initiation_enabled"] is False
    assert status["execution_enabled"] is False
    assert status["sika_reference_balance_is_bank_money"] is False
    assert trial["available"] is True
    assert trial["account"]["balance_type"] == "dummy_data"
    assert trial["sika_view"]["bank_money_claim"] is False
    assert trial["money_moved"] is False


def test_surface_has_bank_trial_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="bankTrialBtn"' in html
    assert 'id="bankTrialSection"' in html


def test_open_banking_red_team_preserves_fail_closed_boundary():
    client = app.test_client()
    body = client.get("/api/sika/open-banking/red-team").get_json()
    assert body["red_team_passed"] is True
    assert body["checks"]["payment_initiation_never_enabled_here"] is True
    assert body["checks"]["customer_funds_never_held_here"] is True
    assert body["checks"]["sika_reference_not_bank_money"] is True
    assert body["checks"]["execution_never_enabled_here"] is True
    assert body["real_payment_ready"] is False
    assert body["money_moved"] is False


def test_surface_has_bank_red_team_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="bankRedTeamBtn"' in html


def test_gbp_to_sika_issue_gate_requires_verified_regulated_receipt():
    client = app.test_client()
    blocked = client.post("/api/sika/value-trial", json={
        "gbp_amount": "25",
        "receipt_id": "r1",
        "bank_reference": "bank-1",
    }).get_json()
    assert blocked["issuance_authorised"] is False
    assert blocked["spendable_sika_created"] is False

    ready = client.post("/api/sika/value-trial", json={
        "gbp_amount": "25",
        "receipt_id": "r2",
        "bank_reference": "bank-2",
        "settlement_verified": True,
        "safeguarding_or_partner_evidence": True,
        "regulatory_basis_verified": True,
    }).get_json()
    assert ready["issuance_authorised"] is True
    assert ready["sika_to_issue"] == "25.00"
    assert ready["external_payment_enabled"] is False


def test_internal_sika_transfer_is_oap_only():
    client = app.test_client()
    body = client.post("/api/sika/internal-transfer/preview", json={
        "amount_sika": "4",
        "sender_balance_sika": "10",
    }).get_json()
    assert body["transfer_allowed"] is True
    assert body["internal_oap_only"] is True
    assert body["bank_transfer_created"] is False
    assert body["external_payment_created"] is False
    assert body["cash_out_created"] is False


def test_surface_has_closed_loop_value_controls():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="valueTrialBtn"' in html
    assert 'id="internalTransferBtn"' in html
    assert 'id="valueSection"' in html


def test_closed_loop_model_never_labels_sika_as_external_bank_payment():
    client = app.test_client()
    body = client.get("/api/sika/value-model").get_json()
    assert body["usage_scope"] == "OAP internal only"
    assert body["external_transfer_supported"] is False
    assert body["cash_out_supported"] is False
    assert body["payment_initiation_supported"] is False
    assert body["regulatory_gate_required"] is True


def test_android_acceptance_gate_stays_closed_without_physical_evidence():
    client = app.test_client()
    body = client.get("/api/sika/android-acceptance").get_json()
    assert body["real_android_pwa_acceptance"] is False
    assert body["public_install_release_gate"] is False
    assert body["signed_native_sika_apk"] is False
    assert body["native_update_recovery_acceptance"] is False


def test_surface_has_android_acceptance_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="androidAcceptanceBtn"' in html
    assert 'id="androidSection"' in html


def test_bank_app_os_alignment_preserves_truth_boundaries():
    client = app.test_client()
    body = client.get("/api/sika/os-alignment").get_json()
    assert body["aligned"] is True
    assert body["bank_app_security"]["scope"] == "SIKA bank app only"
    assert body["bank_app_security"]["founder_auth_touched"] is False
    assert body["bank_app_security"]["founder_password_linked"] is False
    assert body["device"]["esim_profile_provisioned"] is False
    assert body["operating_system"]["generation"] == "Gen0 PWA"
    assert body["operating_system"]["native_android_os"] is False
    assert body["digital_silicon"]["physical_chip_built"] is False
    assert body["organism"]["single_brain"] == "SMI"
    assert body["organism"]["human_authority_final"] is True


def test_surface_has_bank_app_os_alignment_controls_without_founder_auth_links():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="osAlignmentBtn"' in html
    assert 'id="osAlignmentSection"' in html
    assert 'href="/enter-my-world"' not in html
    assert 'href="/activate-founder"' not in html
    assert "Founder authentication is outside this bank-app boundary" in html


def test_deep_dive_21_reuses_canonical_oap_boundaries():
    client = app.test_client()
    body = client.get("/api/sika/deep-dive-21").get_json()
    assert body["depth"] == 21
    assert len(body["mind"]) == 7
    assert len(body["body"]) == 7
    assert len(body["soul"]) == 7
    assert body["single_brain"] == "SMI"
    assert body["human_authority_final"] is True
    assert body["silicon_gate_count"] == 21
    assert body["sika_role"] == "financial/value organ inside OAP"
    assert body["founder_auth_touched"] is False
    assert body["execution_granted"] is False
    assert body["consequential_blocks"]["money_transfer_blocked"] is True
    assert body["consequential_blocks"]["esim_activation_blocked"] is True


def test_surface_has_deep_dive_21_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="deepDive21Btn"' in html
    assert 'id="deepDive21Section"' in html


def test_bank_app_password_is_separate_from_founder_auth_and_never_returned():
    client = app.test_client()
    device = "device-bank-security-test"
    created = client.post("/api/sika/security/password/create", json={
        "device_id": device,
        "password": "strong-bank-app-passphrase",
    })
    assert created.status_code == 201
    body = created.get_json()
    assert body["created"] is True
    assert body["password_hash_returned"] is False
    assert body["founder_auth_touched"] is False
    assert "password_hash" not in body

    wrong = client.post("/api/sika/security/password/unlock", json={
        "device_id": device,
        "password": "wrong-password",
    })
    assert wrong.status_code == 401
    assert wrong.get_json()["unlocked"] is False

    unlocked = client.post("/api/sika/security/password/unlock", json={
        "device_id": device,
        "password": "strong-bank-app-passphrase",
    })
    assert unlocked.status_code == 200
    assert unlocked.get_json()["unlocked"] is True
    assert unlocked.get_json()["founder_auth_touched"] is False

    locked = client.post("/api/sika/security/password/lock", json={"device_id": device})
    assert locked.status_code == 200
    assert locked.get_json()["locked"] is True


def test_bank_app_password_status_is_truthful_about_acceptance_only_storage():
    client = app.test_client()
    response = client.get("/api/sika/security/password/status?device_id=status-device")
    body = response.get_json()
    assert response.status_code == 200
    assert body["storage"] == "process_local_acceptance_only"
    assert body["owner_identity_bound"] is False
    assert body["durable_credential_store"] is False
    assert body["production_ready"] is False
    assert body["founder_auth_touched"] is False


def test_surface_has_bank_app_password_controls_and_no_founder_links():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    for control in ("bankDeviceId","bankPassword","bankPasswordCreateBtn","bankPasswordUnlockBtn","bankPasswordLockBtn"):
        assert f'id="{control}"' in html
    assert 'href="/activate-founder"' not in html
    assert 'href="/enter-my-world"' not in html


def test_owner_device_binding_is_canonical_uuid_scoped_and_founder_auth_isolated():
    client = app.test_client()
    owner = "11111111-1111-4111-8111-111111111111"
    device = "sika-owner-device-test"

    created = client.post("/api/sika/device/bind", json={
        "owner_id": owner,
        "device_id": device,
    })
    assert created.status_code == 201
    body = created.get_json()
    assert body["bound"] is True
    assert body["founder_auth_touched"] is False
    assert body["identity_authority_changed"] is False
    assert body["esim_provisioned"] is False
    assert body["production_ready"] is False

    status = client.get(f"/api/sika/device/status?owner_id={owner}&device_id={device}")
    assert status.status_code == 200
    snapshot = status.get_json()
    assert snapshot["matched"] is True
    assert snapshot["durable"] is False
    assert snapshot["hrm_recorded"] is False

    removed = client.post("/api/sika/device/unbind", json={
        "owner_id": owner,
        "device_id": device,
    })
    assert removed.status_code == 200
    assert removed.get_json()["unbound"] is True


def test_owner_device_binding_rejects_noncanonical_owner():
    client = app.test_client()
    response = client.post("/api/sika/device/bind", json={
        "owner_id": "local-founder",
        "device_id": "device-a",
    })
    assert response.status_code == 400
    assert response.get_json()["bound"] is False


def test_surface_has_owner_device_binding_controls():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    for control in ("bankOwnerId","bankDeviceBindBtn","bankDeviceStatusBtn","bankDeviceUnbindBtn"):
        assert f'id="{control}"' in html


def test_durable_device_binding_reuses_canonical_store_but_public_write_stays_closed():
    client = app.test_client()
    response = client.get("/api/sika/device/durable-readiness")
    body = response.get_json()
    assert response.status_code == 200
    assert body["canonical_store_reused"] is True
    assert body["workspace_id"] == "sika"
    assert body["audit_chain_reused"] is True
    assert body["owner_uuid_required"] is True
    assert body["durable_bind_function_present"] is True
    assert body["durable_recovery_function_present"] is True
    assert body["standalone_public_write_enabled"] is False
    assert body["authenticated_host_required"] is True
    assert body["founder_auth_touched"] is False
    assert body["production_ready"] is False


def test_surface_has_durable_device_binding_readiness_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="bankDeviceDurableBtn"' in html


def test_authenticated_owner_adapter_readiness_rejects_public_owner_trust():
    client = app.test_client()
    response = client.get("/api/sika/owner-session/readiness")
    body = response.get_json()
    assert response.status_code == 200
    assert body["adapter_present"] is True
    assert body["required_identity_source"] == "oap_authenticated_session"
    assert body["caller_supplied_owner_id_trusted"] is False
    assert body["durable_bind_available_after_server_auth_resolution"] is True
    assert body["durable_recovery_available_after_server_auth_resolution"] is True
    assert body["standalone_public_mutation_exposed"] is False
    assert body["founder_auth_touched"] is False
    assert body["production_ready"] is False


def test_surface_has_authenticated_owner_bridge_readiness_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="bankOwnerSessionBtn"' in html


def test_deep_dive_21_reports_new_bank_security_capabilities_without_fake_production_green():
    client = app.test_client()
    body = client.get("/api/sika/deep-dive-21").get_json()
    assert body["bank_app_password_software_ready"] is True
    assert body["bank_app_password_durable_store_ready"] is True
    assert body["device_binding_software_ready"] is True
    assert body["durable_device_binding_store_ready"] is True
    assert body["authenticated_owner_bridge_ready"] is True
    assert body["production_owner_session_route_software_ready"] is True
    assert body["production_owner_session_route_live_proof"] is False
    assert body["physical_android_acceptance"] is False
    assert body["real_payment_ready"] is False
    assert body["execution_granted"] is False


def test_durable_bank_credential_store_reuses_canonical_sika_store_without_public_write():
    client = app.test_client()
    response = client.get("/api/sika/security/credential-store/readiness")
    body = response.get_json()
    assert response.status_code == 200
    assert body["canonical_store_reused"] is True
    assert body["workspace_id"] == "sika"
    assert body["hash_algorithm"] == "scrypt"
    assert body["plaintext_password_stored"] is False
    assert body["password_hash_returned"] is False
    assert body["durable_create_function_present"] is True
    assert body["durable_verify_function_present"] is True
    assert body["durable_recovery_function_present"] is True
    assert body["standalone_public_write_enabled"] is False
    assert body["authenticated_host_required"] is True
    assert body["founder_auth_touched"] is False
    assert body["production_ready"] is False


def test_deep_dive_21_now_reports_durable_bank_credential_store_ready():
    client = app.test_client()
    body = client.get("/api/sika/deep-dive-21").get_json()
    assert body["bank_app_password_software_ready"] is True
    assert body["bank_app_password_durable_store_ready"] is True
    assert body["production_owner_session_route_software_ready"] is True
    assert body["production_owner_session_route_live_proof"] is False
    assert body["real_payment_ready"] is False


def test_surface_has_durable_bank_credential_readiness_control():
    client = app.test_client()
    html = client.get("/sika").get_data(as_text=True)
    assert 'id="bankCredentialStoreBtn"' in html


def test_owner_session_readiness_separates_software_from_live_proof():
    client = app.test_client()
    body = client.get("/api/sika/owner-session/readiness").get_json()
    assert body["authenticated_host_route_software_ready"] is True
    assert body["authenticated_host_route_live_proof"] is False
    assert body["production_ready"] is False


def test_sika_scam_preflight_flags_safe_account_and_remote_access():
    client = app.test_client()
    response = client.post(
        "/api/sika/fraud/preflight",
        json={
            "amount_sika": "250",
            "new_recipient": True,
            "safe_account_claim": True,
            "remote_access_or_screen_share": True,
        },
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["scam_detected"] is True
    assert body["decision"] == "block_software_only"
    assert "safe_account_claim" in body["reasons"]
    assert "remote_access_or_screen_share" in body["reasons"]
    assert body["money_moved"] is False
    assert body["regulated_execution_authorised"] is False


def test_sika_security_posture_does_not_fake_web_screenshot_block():
    client = app.test_client()
    response = client.get("/api/sika/security/posture")
    body = response.get_json()
    assert response.status_code == 200
    assert body["screen_capture"]["web_os_level_block_enforceable"] is False
    assert body["screen_capture"]["browser_capture_claim_allowed"] is False
    assert body["screen_capture"]["visibility_blur_enabled"] is True
    assert body["screen_capture"]["display_capture_permission_disabled"] is True
    assert body["fraud_and_scam"]["safe_account_signal"] is True
    assert body["money_execution_enabled"] is False
    assert body["founder_auth_touched"] is False


def test_sika_session_policy_is_fail_closed_and_founder_untouched():
    client = app.test_client()
    response = client.get("/api/sika/security/session-policy")
    body = response.get_json()
    assert response.status_code == 200
    assert body["idle_timeout_seconds"] == 300
    assert body["sensitive_action_reauth_seconds"] == 120
    assert body["reauth_required_after_timeout"] is True
    assert body["founder_auth_touched"] is False
    assert body["money_execution_enabled"] is False


def test_sika_payment_controls_enforce_cooling_off_limit_and_suspicious_device():
    client = app.test_client()
    response = client.post(
        "/api/sika/security/payment-controls",
        json={
            "amount_sika": "200",
            "daily_used_sika": "900",
            "daily_limit_sika": "1000",
            "recipient_age_minutes": 5,
            "suspicious_device": True,
        },
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["over_limit"] is True
    assert body["new_recipient_cooling_off"] is True
    assert body["suspicious_device"] is True
    assert body["step_up_required"] is True
    assert body["payment_may_progress_to_review"] is False
    assert body["money_moved"] is False
    assert body["executable"] is False


def test_sika_security_ledger_readiness_is_fail_closed():
    client = app.test_client()
    response = client.get("/api/sika/security/posture")
    assert response.status_code == 200
    body = response.get_json()
    assert body["money_execution_enabled"] is False
    assert body["founder_auth_touched"] is False
