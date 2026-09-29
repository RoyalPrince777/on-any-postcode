from mission_control.smi_chat_runtime import _safe_runtime_error_code


def test_provider_runtime_diagnostic_allow_list_preserves_known_machine_codes():
    assert _safe_runtime_error_code(RuntimeError("provider_unavailable")) == "provider_unavailable"
    assert _safe_runtime_error_code(RuntimeError("local_inference_unavailable")) == "local_inference_unavailable"
    assert _safe_runtime_error_code(RuntimeError("home_node_worker_unavailable")) == "home_node_worker_unavailable"


def test_provider_runtime_diagnostic_collapses_dynamic_http_status():
    assert _safe_runtime_error_code(RuntimeError("provider_http_401")) == "provider_http_error"
    assert _safe_runtime_error_code(RuntimeError("provider_http_503")) == "provider_http_error"


def test_provider_runtime_diagnostic_never_echoes_arbitrary_exception_text():
    secret_like = "sk-proj-example-secret-value-that-must-never-leak"
    assert _safe_runtime_error_code(RuntimeError(secret_like)) == "provider_runtime_error"
    assert secret_like not in _safe_runtime_error_code(RuntimeError(secret_like))
