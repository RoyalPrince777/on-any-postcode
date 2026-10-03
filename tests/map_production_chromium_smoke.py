"""Live production Chromium proof for OAP Maps.

No fixtures, request interception, set_content(), or mocked road geometry.
The target must be the deployed public /oap-map route.
"""
from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

TARGET = os.environ.get("OAP_MAP_URL", "https://on-any-postcode.onrender.com/oap-map").strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 393, "height": 852},
        is_mobile=True,
        has_touch=True,
        device_scale_factor=2,
        user_agent=(
            "Mozilla/5.0 (Linux; Android 15; Pixel 8) "
            "AppleWebKit/537.36 Chrome/130 Mobile Safari/537.36"
        ),
    )
    page = context.new_page()
    page_errors: list[str] = []
    failed_requests: list[str] = []
    asset_status: dict[str, int] = {}

    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on("requestfailed", lambda request: failed_requests.append(request.url))
    page.on(
        "response",
        lambda response: asset_status.__setitem__(response.url, response.status)
        if "/map-intelligence/assets/" in response.url
        else None,
    )

    response = page.goto(TARGET, wait_until="domcontentloaded", timeout=60000)
    assert response is not None and response.status == 200, (
        "map_navigation_failed",
        None if response is None else response.status,
    )

    app = page.locator(".map-app")
    roads_svg = page.locator("#roads-svg")
    boot = page.locator("#oap-map-boot")

    assert app.is_visible(), "map_app_not_visible"
    box = app.bounding_box()
    assert box and box["width"] >= 300 and box["height"] >= 500, ("map_app_zero_or_tiny", box)
    assert roads_svg.is_visible(), "roads_svg_not_visible"

    required_assets = (
        "oap_map_navigation.css",
        "oap_map_navigation.js",
        "oap_os_map_bridge.js",
    )

    api_line_counts = page.evaluate(
        """async () => {
          const urls = [
            '/map-intelligence/road-geometry/14/8182/5455?profile=driving',
            '/map-intelligence/road-geometry/14/8181/5456?profile=driving',
            '/map-intelligence/road-geometry/14/8183/5455?profile=driving'
          ];
          const counts = [];
          for (const url of urls) {
            try {
              const response = await fetch(url, {credentials:'same-origin', cache:'no-store'});
              if (!response.ok) { counts.push(-response.status); continue; }
              const payload = await response.json();
              counts.push(Number(payload.line_count || 0));
            } catch (error) {
              counts.push(-1);
            }
          }
          return counts;
        }"""
    )
    assert any(count > 0 for count in api_line_counts), ("road_geometry_api_empty", api_line_counts)
    page.wait_for_function(
        "() => document.querySelector('#oap-map-boot')?.hidden === true",
        timeout=30000,
    )
    page.wait_for_function(
        "() => document.querySelectorAll('#road-layer polyline').length > 0",
        timeout=30000,
    )

    for asset in required_assets:
        matches = [status for url, status in asset_status.items() if url.endswith("/" + asset)]
        assert matches and all(status == 200 for status in matches), (asset, matches)

    road_count = page.locator("#road-layer polyline").count()
    assert road_count > 0, "no_live_road_polylines"
    assert boot.is_hidden(), "map_boot_state_did_not_clear"
    assert not page_errors, ("browser_page_errors", page_errors)
    road_request_failures = [
        url for url in failed_requests
        if "/map-intelligence/road-geometry/" in url
    ]

    print(
        "OAP_MAP_PRODUCTION_BROWSER_PASS",
        f"url={TARGET}",
        f"roads={road_count}",
        f"box={box['width']}x{box['height']}",
        f"road_request_failures={len(road_request_failures)}",
        f"api_line_counts={api_line_counts}",
    )
    context.close()
    browser.close()
