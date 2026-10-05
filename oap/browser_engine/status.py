"""Machine-readable truth boundary for the software-only OAP Engine mission."""
from __future__ import annotations


def status() -> dict[str, object]:
    return {
        "engine": "OAP_ENGINE",
        "contract_version": 1,
        "physical_scope_excluded": True,
        "general_web_default_renderer": "Android System WebView",
        "standards_complete": False,
        "implemented": {
            "html_dom": "BOUNDED",
            "css_cascade": "BOUNDED",
            "layout": "BOUNDED",
            "paint": "BOUNDED_TEXT_BACKGROUND_WEIGHT",
            "display_list": "BOUNDED",
            "origin_model": "HTTP_HTTPS_BOUNDED",
            "python_origin_storage": "IN_PROCESS_QUOTA_BOUNDED",
            "android_origin_storage": "APP_LOCAL_DURABLE_QUOTA_BOUNDED",
            "accessibility_engine": "BOUNDED_METADATA",
            "accessibility_android": "PAGE_SUMMARY_BOUNDED",
            "forms": "MODEL_PLUS_CERTIFIED_GET_SEARCH_SUBMISSION",
            "response_cache": "IN_MEMORY_LRU_BOUNDED",
            "cookies": "HOST_ONLY_BOUNDED",
            "network_request_policy": "HTTP_HTTPS_GET_HEAD_POST_BOUNDED",
            "android_native_surface": True,
            "supported_page_auto_routing": ("/", "/world", "/search"),
            "webview_fallback": True,
            "malformed_input_stress_proof": True,
        },
        "unbuilt": (
            "standards_complete_javascript_vm",
            "general_arbitrary_web_fetch_pipeline",
            "full_css_layout_flex_grid_positioning",
            "gpu_raster_compositor",
            "images_fonts_media_stack",
            "per_node_android_accessibility_virtual_tree",
            "general_form_submission_runtime",
            "service_workers",
            "webrtc",
            "webgl_webgpu",
            "process_site_isolation",
            "wpt_scale_compatibility",
            "general_webview_replacement",
        ),
        "human_authority_final": True,
    }
