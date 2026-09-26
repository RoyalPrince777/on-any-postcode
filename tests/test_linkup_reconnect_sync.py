from pathlib import Path


def test_link_message_sync_schema_is_explicit_and_serialized():
    source = Path("mission_control/link_message_sync.py").read_text(encoding="utf-8")

    assert "ALTER TABLE messages ADD COLUMN IF NOT EXISTS client_message_id UUID" in source
    assert "uq_messages_sender_client" in source
    assert "idx_messages_pair_created_id" in source
    assert "pg_advisory_xact_lock" in source


def test_link_send_accepts_client_message_id_for_idempotency():
    routes = Path("mission_control/link_message_routes.py").read_text(encoding="utf-8")
    store = Path("mission_control/product_store.py").read_text(encoding="utf-8")

    assert 'client_message_id=payload.get("client_message_id")' in routes
    assert "client_message_id: object = None" in store
    assert "client_message_id_conflict" in store
    assert "ON CONFLICT (sender_id,client_message_id)" in store


def test_retry_lookup_precedes_rate_limit():
    source = Path("mission_control/product_store.py").read_text(encoding="utf-8")

    lookup = source.index("WHERE sender_id=%s AND client_message_id=%s LIMIT 1")
    rate = source.index("linkup_rate_limit", lookup)
    assert lookup < rate


def test_stable_cursor_uses_timestamp_and_message_id():
    source = Path("mission_control/product_store.py").read_text(encoding="utf-8")
    routes = Path("mission_control/link_message_routes.py").read_text(encoding="utf-8")

    assert "after_id: object = None" in source
    assert "incomplete_message_cursor" in source
    assert "created_at=%s::timestamptz" in source
    assert "id>%s::uuid" in source
    assert "ORDER BY created_at ASC,id ASC" in source
    assert 'after_id=request.args.get("after_id", "")' in routes


def test_browser_reconnect_reuses_same_client_id_without_persistent_body_storage():
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")

    assert 'typeof crypto !== "undefined"' in script
    assert 'typeof crypto.randomUUID === "function"' in script
    assert "crypto.randomUUID()" in script
    assert "pendingRetries" in script
    assert 'window.addEventListener("online"' in script
    assert "pending.payload" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "indexedDB" not in script


def test_interrupted_retry_never_falls_back_to_changed_composer():
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")
    guard = script.split("const sendLink = async (form, fixedPayload = null) => {", 1)[1]
    readiness = guard.split("const textarea = bodyFor(form);", 1)[0]
    assert "if (fixedPayload) {" in readiness
    assert "showRetry(form, fixedPayload," in readiness
    assert readiness.index("if (fixedPayload) {") < readiness.index("form.submit();")
    assert "pending.payload" in script
    assert "localStorage" not in script


def test_sync_rollout_falls_back_before_schema_activation():
    source = Path("mission_control/product_store.py").read_text(encoding="utf-8")
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")

    assert 'INSERT INTO messages(sender_id,recipient_id,body)' in source
    assert "state.syncReady &&" in script
    assert 'typeof crypto !== "undefined"' in script
    assert 'typeof crypto.randomUUID === "function"' in script
    assert "status.idempotent_send === true && status.stable_cursor === true" in script


def test_explicit_sync_activation_commands_exist():
    source = Path("mission_control/__init__.py").read_text(encoding="utf-8")

    assert "OAP_LINK_MESSAGE_SYNC_MIGRATION_ON_BOOT" in source
    assert "oap-link-message-sync-status" in source
    assert "oap-init-link-message-sync" in source


def test_permission_denials_cannot_be_retried_or_queued_after_reconnect():
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")
    denied = script.split('if (code === "link_blocked" || code === "accepted_link_required") {', 1)[1]
    terminal = denied.split("} else if (", 1)[0]
    retry = denied.split("} else if (", 1)[1]
    assert "state.pendingRetries.delete(payload.client_message_id)" in terminal
    assert "localStatus.textContent = message;" in terminal
    assert "showRetry(" not in terminal
    assert "state.pendingRetries.set(payload.client_message_id" in retry
    assert "showRetry(form, payload, message)" in retry
    assert 'code === "link_blocked"' in script
    assert 'code === "accepted_link_required"' in script
    assert 'window.addEventListener("online"' in script


def test_live_acceptance_receipt_is_owner_scoped_and_content_free():
    store = Path("mission_control/product_store.py").read_text(encoding="utf-8")
    routes = Path("mission_control/link_message_routes.py").read_text(encoding="utf-8")

    assert "def message_acceptance_receipt(" in store
    assert "WHERE id=%s AND sender_id=%s" in store
    assert '"persisted": True' in store
    assert '"landed": True' in store
    assert '"seen": row[1] is not None' in store
    assert '"content_included": False' in store
    assert '"owner_scoped": True' in store
    assert '"body"' not in store.split("def message_acceptance_receipt(", 1)[1].split("def peer_messages_since(", 1)[0]
    assert '@bp.get("/linkup/messages/<message_id>/acceptance")' in routes
    assert "@web_security.login_required(api=True)" in routes
    assert "product_store.message_acceptance_receipt(identity, message_id)" in routes


def test_acceptance_receipt_does_not_fake_reconnect_proof():
    store = Path("mission_control/product_store.py").read_text(encoding="utf-8")

    receipt = store.split("def message_acceptance_receipt(", 1)[1].split("def peer_messages_since(", 1)[0]
    assert '"reconnect_readback_capable": row[3] is not None' in receipt
    assert "reconnect_proven" not in receipt
