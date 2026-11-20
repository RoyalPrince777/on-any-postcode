from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import app as app_module
from mission_control import third_eye_intelligence, web_security

NOW = datetime(2026, 11, 20, 1, 0, tzinfo=UTC)
T = int(NOW.timestamp() * 1000)


def feed(generated=T):
    return {
        "type": "FeatureCollection",
        "metadata": {"generated": generated},
        "features": [
            {
                "type": "Feature",
                "properties": {"place": "Near Testville", "mag": 3.2, "time": T},
                "geometry": {"coordinates": [-0.15, 51.5, 4.0]},
            }
        ],
    }


def test_status_never_infers_camera_or_full_runtime():
    status = third_eye_intelligence.status()
    assert status["founder_private_only"] is True
    assert status["public_route_allowed"] is False
    assert status["sources"]["public_cameras"]["live_feed_proven"] is False
    assert status["sources"]["3d_globe"]["render_proven"] is False
    assert status["upstream_reference"]["upstream_code_imported"] is False
    assert status["full_third_eye_ready"] is False
    assert status["individual_tracking"] is False


def test_fresh_attributed_earth_observation():
    result = third_eye_intelligence.parse_usgs_feed(feed(), now=NOW)
    assert result["feed_verified"] is True
    assert result["freshness"] == "fresh"
    assert result["events"][0]["latitude"] == 51.5
    assert result["full_third_eye_ready"] is False


def test_stale_and_future_provenance_never_count_as_live():
    for generated in (T - 900_001, T + 30_000):
        result = third_eye_intelligence.parse_usgs_feed(feed(generated), now=NOW)
        assert result["freshness"] == "stale"
        assert result["live_claim_allowed"] is False


def test_undated_or_incorrect_feed_fails_closed():
    for payload in ({"type": "FeatureCollection", "metadata": {}, "features": []}, [], {}, None):
        try:
            third_eye_intelligence.parse_usgs_feed(payload, now=NOW)
        except ValueError:
            pass
        else:
            raise AssertionError("unattributed data must fail closed")


def test_invalid_geography_is_ignored_and_events_bounded():
    payload = feed()
    payload["features"] *= 30
    payload["features"][0]["geometry"]["coordinates"] = [900, 91]
    result = third_eye_intelligence.parse_usgs_feed(payload, now=NOW)
    assert result["events"] == []
    assert result["event_count_returned"] == 0


def test_network_failure_returns_unavailable_without_live_claim():
    with patch.object(third_eye_intelligence, "urlopen", side_effect=TimeoutError("No network")):
        result = third_eye_intelligence.latest_earthquakes()
    assert result["feed_verified"] is False
    assert result["events"] == []
    assert result["live_claim_allowed"] is False


def test_private_routes_have_existing_founder_auth_metadata():
    for endpoint in ("alignment.smi_third_eye_status", "alignment.smi_third_eye_earthquakes"):
        view = app_module.app.view_functions[endpoint]
        assert view._oap_login_required is True
        assert view._oap_founder_only is True
        assert view._oap_api is True


def test_anonymous_earth_and_status_requests_are_denied(client, monkeypatch):
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    for path in ("/mission/smi/third-eye/status", "/mission/smi/third-eye/earthquakes"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"
        assert response.headers["Cache-Control"] == "no-store"


def test_founder_authorised_status_is_read_only_and_uncached(client, monkeypatch):
    monkeypatch.setattr(
        web_security, "current_authenticated_user",
        lambda: {"id": "00000000-0000-4000-8000-000000000001"},
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    response = client.get("/mission/smi/third-eye/status")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    state = response.get_json()
    assert state["founder_private_only"] is True
    assert state["camera_view"]["device_camera_started"] is False
    assert state["sources"]["earthquakes"]["feed_proven"] is False


def test_third_eye_is_one_tool_in_smi_not_a_public_duplicate():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    template = (root / "templates" / "ollama_chat.html").read_text(encoding="utf-8")
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    assert "thirdEyeStatusUrl:" in template
    assert "thirdEyeEarthquakesUrl:" in template
    assert "filename='smi_third_eye.js'" in template
    assert "smi-third-eye-menu-button" in script
    assert "attach-menu" in script
    assert "smi-third-eye-panel" in script
    assert "credentials: \"same-origin\"" in script
    assert "cache: \"no-store\"" in script
    assert "events.replaceChildren()" in script
    assert "li.textContent" in script
    assert "getUserMedia" not in script
    assert "getCurrentPosition" not in script
    assert "setInterval" not in script
    assert "Full Third Eye ready" not in script


def test_third_eye_seven_views_are_nested_inside_one_smi_tool():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    css = (root / "static" / "smi_third_eye.css").read_text(encoding="utf-8")

    for name in (
        "Earth Vision",
        "Ground Vision",
        "Air Vision",
        "Space Vision",
        "Earth Intelligence",
        "SMI Analysis",
        "Controls",
    ):
        assert f'name: "{name}"' in script
    assert 'id="smi-third-eye-internal-menu"' in script
    assert 'id="smi-third-eye-back"' in script
    assert "internalMenu.appendChild(button)" in script
    assert script.count("menu.appendChild(menuButton)") == 1
    assert "smi-third-eye-menu-item" in css
    assert 'document.getElementById("faceup-button")' in script
    assert "getUserMedia" not in script
    assert "setInterval" not in script


def test_third_eye_internal_layout_mobile_navigation_and_truth_states():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    css = (root / "static" / "smi_third_eye.css").read_text(encoding="utf-8")

    assert 'id="smi-third-eye-home"' in script
    assert 'id="smi-third-eye-detail"' in script
    assert 'id="smi-third-eye-detail-state"' in script
    assert 'id="smi-third-eye-crumb"' in script
    assert 'id="smi-third-eye-status"' in script
    assert 'aria-label="Inside Third Eye"' in script
    assert 'aria-live="polite"' in script
    assert 'event.key === "Escape"' in script
    assert "menuButton.focus()" in script
    assert "home.hidden = true" in script
    assert "home.hidden = false" in script
    assert "stopRequest(true)" in script
    assert "requestKind = \"status\"" in script
    assert "requestKind = \"earth\"" in script
    assert "id === \"ground\"" in script
    assert "getUserMedia" not in script
    assert "setInterval" not in script
    assert "public_cameras?.live_feed_proven === false" in script
    assert "min-height:44px" in css
    assert "max-height:72dvh" in css
    assert "prefers-reduced-motion" in css
    assert "focus-visible" in css


def test_third_eye_live_weather_reuses_existing_ecosystem_source():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    template = (root / "templates" / "ollama_chat.html").read_text(encoding="utf-8")
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    css = (root / "static" / "smi_third_eye.css").read_text(encoding="utf-8")

    assert "thirdEyeWeatherUrl:{{ url_for('ecosystem_intelligence.source_location_weather')|tojson }}" in template
    assert "new URL(config.thirdEyeWeatherUrl, window.location.origin)" in script
    assert 'url.origin !== window.location.origin' in script
    assert 'url.searchParams.set("location", place)' in script
    assert 'item?.source === "oap_weather_live_source"' in script
    assert "data?.weather_environment_proven !== true" in script
    assert 'observation.live_claim_allowed === true && freshness === "fresh"' in script
    assert 'observation?.observed_at' in script
    assert 'requestKind = "weather"' in script
    assert "li.textContent" in script
    assert "getCurrentPosition" not in script
    assert "setInterval" not in script
    assert ".smi-third-eye-place{" in css


def _tfl_camera(camera_id="00001.00001", *, available="true", image=None):
    return {
        "id": "JamCams_" + camera_id,
        "commonName": "Westminster Road",
        "lat": 51.5072,
        "lon": -0.1276,
        "additionalProperties": [
            {"key": "available", "value": available},
            {"key": "imageUrl", "value": image or (
                third_eye_intelligence.TFL_IMAGE_PREFIX + camera_id + ".jpg"
            )},
        ],
    }


def test_real_london_camera_catalogue_accepts_only_available_vetted_public_stills():
    rows = [
        _tfl_camera(),
        _tfl_camera("00001.00002", available="false"),
        _tfl_camera("00001.00003", image="https://example.invalid/private.jpg"),
        {**_tfl_camera("00001.00004"), "lat": 900},
    ]
    cameras = third_eye_intelligence.parse_london_jamcams(rows)
    assert [cam["id"] for cam in cameras] == ["00001.00001"]
    assert cameras[0]["name"] == "Westminster Road"
    assert all("imageUrl" not in cam for cam in cameras)


def test_tfl_jamcam_catalogue_source_can_fail_closed_without_fabricated_live_state(monkeypatch):
    third_eye_intelligence._TFL_CACHE = None
    monkeypatch.setattr(
        third_eye_intelligence, "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("upstream unavailable")),
    )
    result = third_eye_intelligence.london_jamcams()
    assert result["source_verified"] is False
    assert result["cameras"] == []
    assert result["continuous_live_video"] is False


def test_unknown_camera_id_cannot_trigger_external_fetch(monkeypatch):
    monkeypatch.setattr(
        third_eye_intelligence, "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not fetch")),
    )
    assert third_eye_intelligence.london_jamcam_frame("http://localhost/secret") is None
    assert third_eye_intelligence.london_jamcam_frame("../../etc/passwd") is None


def test_public_london_cameras_have_existing_founder_auth_and_deny_anonymous(client, monkeypatch):
    for endpoint in ("alignment.smi_third_eye_london_cameras", "alignment.smi_third_eye_london_frame"):
        view = app_module.app.view_functions[endpoint]
        assert view._oap_login_required is True
        assert view._oap_founder_only is True
        assert view._oap_api is True
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    for path in (
        "/mission/smi/third-eye/london/cameras",
        "/mission/smi/third-eye/london/frame/00001.00001",
    ):
        response = client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"


def test_london_jamcam_ui_is_same_origin_manual_and_attributed():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    template = (root / "templates" / "ollama_chat.html").read_text(encoding="utf-8")
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    assert "thirdEyeLondonCamerasUrl:{{ url_for('alignment.smi_third_eye_london_cameras')|tojson }}" in template
    assert "thirdEyeLondonFrameUrl:{{ url_for('alignment.smi_third_eye_london_frame'" in template
    assert "requestKind = \"london\"" in script
    assert "function loadLondonCameras(" in script
    assert "function showLondonCamera(" in script
    assert "cameraImage.src = base.toString()" in script
    assert "base.origin !== window.location.origin" in script
    assert "Powered by TfL Open Data" in script
    assert "Capture time not supplied" in script
    assert "getUserMedia" not in script
    assert "setInterval" not in script


def test_tfl_video_is_offered_only_for_vetted_mp4_metadata():
    camera = _tfl_camera()
    camera["additionalProperties"].append({
        "key": "videoUrl",
        "value": third_eye_intelligence.TFL_IMAGE_PREFIX + "00001.00001.mp4",
    })
    valid = third_eye_intelligence.parse_london_jamcams([camera])[0]
    assert valid["clip_available"] is True
    camera["additionalProperties"][-1]["value"] = "https://example.invalid/clip.mp4"
    unapproved = third_eye_intelligence.parse_london_jamcams([camera])[0]
    assert unapproved["clip_available"] is False


def test_tfl_rolling_clip_checks_catalogue_source_type_and_bounded_bytes(monkeypatch):
    camera_id = "00001.00001"
    camera = {"id": camera_id, "clip_available": True}
    monkeypatch.setattr(third_eye_intelligence, "_TFL_CACHE", (float("inf"), [camera]))
    monkeypatch.setattr(
        third_eye_intelligence, "london_jamcams", lambda: {"source_verified": True}
    )
    sample = bytes([0, 0, 0, 28]) + b"ftypisom0000"

    class Headers:
        def get_content_type(self):
            return "video/mp4"

        def get(self, key):
            return None

    class Response:
        status = 200
        headers = Headers()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def geturl(self):
            return third_eye_intelligence.TFL_IMAGE_PREFIX + camera_id + ".mp4"

        def read(self, amount):
            return sample[:amount]

    monkeypatch.setattr(third_eye_intelligence, "urlopen", lambda *args, **kwargs: Response())
    received = third_eye_intelligence.london_jamcam_clip(camera_id)
    assert received is not None
    assert received[0] == sample
    assert received[1] is None

    monkeypatch.setattr(third_eye_intelligence, "_TFL_CACHE", (float("inf"), [
        {"id": camera_id, "clip_available": False}
    ]))
    assert third_eye_intelligence.london_jamcam_clip(camera_id) is None


def test_london_rolling_clip_route_remains_founder_private(client, monkeypatch):
    view = app_module.app.view_functions["alignment.smi_third_eye_london_clip"]
    assert view._oap_login_required is True
    assert view._oap_founder_only is True
    assert view._oap_api is True
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    response = client.get("/mission/smi/third-eye/london/clip/00001.00001")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_london_real_mp4_control_is_user_initiated_and_stops_on_exit():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    template = (root / "templates" / "ollama_chat.html").read_text(encoding="utf-8")
    assert "thirdEyeLondonClipUrl:{{ url_for('alignment.smi_third_eye_london_clip'" in template
    assert 'id="smi-third-eye-camera-video"' in script
    assert 'preload="none"' in script
    assert "camera?.clip_available === true" in script
    assert "cameraVideo.src = clipUrl.toString()" in script
    assert "cameraVideo.pause()" in script
    assert "clearCameraMedia()" in script
    assert "cameraVideo.play()" in script
    assert "autoplay" not in script


def test_london_camera_catalogue_is_cr4_first_and_not_limited_to_fifteen(monkeypatch):
    rows = [
        {
            "id": f"00001.{index:05d}",
            "name": f"Camera {index}",
            "latitude": 51.4026 + index * 0.001,
            "longitude": -0.14516,
            "clip_available": False,
        }
        for index in range(45)
    ]
    monkeypatch.setattr(third_eye_intelligence, "_TFL_CACHE", (float("inf"), rows))
    first = third_eye_intelligence.london_jamcams(search="CR4", page=1)
    second = third_eye_intelligence.london_jamcams(page=2)
    third = third_eye_intelligence.london_jamcams(page=3)
    assert first["source_verified"] is True
    assert first["origin"]["label"] == "CR4 / Mitcham district"
    assert first["origin"]["precision"] == "district_reference_not_device"
    assert first["sort"] == "distance_from_cr4_nearest_first"
    assert first["total_matching"] == 45
    assert len(first["cameras"]) == 20
    assert len(second["cameras"]) == 20
    assert len(third["cameras"]) == 5
    assert first["cameras"][0]["id"] == "00001.00000"
    assert first["cameras"][0]["distance_km"] == 0.0
    assert second["cameras"][0]["id"] == "00001.00020"
    assert first["has_more"] is True
    assert second["has_previous"] is True
    assert third["has_more"] is False


def test_cr4_nearby_radius_fails_to_fabricate_cameras(monkeypatch):
    rows = [{
        "id": "00001.00001",
        "name": "Only far away road",
        "latitude": 51.6,
        "longitude": 0.0,
        "clip_available": False,
    }]
    monkeypatch.setattr(third_eye_intelligence, "_TFL_CACHE", (float("inf"), rows))
    nearby = third_eye_intelligence.london_jamcams(radius_km=5)
    london = third_eye_intelligence.london_jamcams(radius_km=0)
    assert nearby["cameras"] == []
    assert nearby["total_matching"] == 0
    assert nearby["source_verified"] is True
    assert len(london["cameras"]) == 1
    assert london["cameras"][0]["distance_km"] > 5
    assert nearby["continuous_live_video"] is False


def test_london_catalogue_bad_paging_and_radius_are_rejected(client, monkeypatch):
    monkeypatch.setattr(
        web_security, "current_authenticated_user",
        lambda: {"id": "00000000-0000-4000-8000-000000000001"},
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    for query in ("page=-3", "page=abc", "radius_km=999", "radius_km=-5"):
        response = client.get("/mission/smi/third-eye/london/cameras?" + query)
        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "invalid_camera_catalogue_selection"


def test_cr4_mobile_camera_list_pages_all_available_public_tfl_sources():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "mission_control"
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    css = (root / "static" / "smi_third_eye.css").read_text(encoding="utf-8")
    assert '"All London · nearest CR4 first"' in script
    assert '"Within 5 km of CR4"' in script
    assert '"Within 15 km of CR4"' in script
    assert '"Within 30 km of CR4"' in script
    assert 'url.searchParams.set("page", String(page))' in script
    assert 'url.searchParams.set("radius_km", String(radiusKm))' in script
    assert "data.has_more === true" in script
    assert "Next 20" in script
    assert "Previous 20" in script
    assert "cam.distance_km.toFixed(1)" in script
    assert "data.cameras.slice(0, 12)" not in script
    assert "cameraImage.src = base.toString()" in script
    assert "setInterval" not in script
    assert ".smi-third-eye-pages{" in css


def test_london_adsb_source_validates_observation_time_and_location():
    timestamp = NOW.timestamp()
    payload = {
        "now": timestamp,
        "ac": [
            {"lat": 51.4, "lon": -0.145, "seen_pos": 5, "flight": "TEST123 ",
             "alt_baro": 13500},
            {"lat": 60.0, "lon": 20.0, "seen_pos": 3, "flight": "OUT"},
            {"lat": 51.4, "lon": -0.145, "seen_pos": 900, "flight": "OLD"},
        ],
    }
    result = third_eye_intelligence.parse_london_aircraft(payload, now=NOW)
    assert result["provider"] == "adsb.lol"
    assert result["freshness"] == "fresh"
    assert result["live_claim_allowed"] is True
    assert len(result["positions"]) == 1
    assert result["positions"][0]["callsign"] == "TEST123"
    assert result["positions"][0]["position_age_seconds"] == 5
    result = third_eye_intelligence.parse_london_aircraft(
        {**payload, "now": timestamp - 500}, now=NOW
    )
    assert result["freshness"] == "stale"
    assert result["live_claim_allowed"] is False


def test_iss_position_is_dated_and_not_mislabelled_london_overflight():
    payload = {
        "id": 25544, "timestamp": NOW.timestamp(),
        "latitude": 48.0, "longitude": 12.0, "altitude": 418.3,
    }
    result = third_eye_intelligence.parse_iss_position(payload, now=NOW)
    assert result["live_claim_allowed"] is True
    assert result["satellite"].startswith("International Space Station")
    assert result["is_over_london"] is False
    assert result["latitude"] == 48.0
    stale = third_eye_intelligence.parse_iss_position(
        {**payload, "timestamp": NOW.timestamp() - 300}, now=NOW
    )
    assert stale["freshness"] == "stale"
    assert stale["live_claim_allowed"] is False
    try:
        third_eye_intelligence.parse_iss_position(
            {**payload, "id": 1}, now=NOW
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unverified ISS ID was accepted")


def test_celestrak_orbit_elements_are_source_dated_not_live_positions():
    stamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    sample = (
        "NORAD_CAT_ID,EPOCH,INCLINATION,MEAN_MOTION,ECCENTRICITY\n"
        f"25544,{stamp},51.6,15.5,0.00015\n"
    ).encode("utf-8")
    result = third_eye_intelligence.parse_celestrak_iss_csv(sample)
    assert result["provider"] == "CelesTrak"
    assert result["element_epoch"] == stamp
    assert result["position_propagated"] is False
    assert result["live_claim_allowed"] is False
    assert result["elements"]["inclination"] == 51.6


def test_nasa_london_imagery_wms_request_fixed_bbox_and_past_date(monkeypatch):
    monkeypatch.setattr(third_eye_intelligence, "_THIRD_EYE_SOURCE_CACHE", {})
    calls = []

    def get_fixed(url, accept, limit, timeout=6):
        calls.append((url, accept, limit))
        return b"\xff\xd8\xffNASA_JPEG_PAYLOAD", "image/jpeg"

    monkeypatch.setattr(third_eye_intelligence, "_fixed_download", get_fixed)
    result = third_eye_intelligence.nasa_london_imagery("2026-11-18")
    assert result is not None
    assert result.startswith(b"\xff\xd8\xff")
    assert len(calls) == 1
    assert calls[0][0].startswith(third_eye_intelligence.NASA_GIBS_WMS + "?")
    assert "MODIS_Terra_CorrectedReflectance_TrueColor" in calls[0][0]
    assert "2026-11-18" in calls[0][0]
    assert "%2C51.25%2C0.25%2C51.72" in calls[0][0]
    assert third_eye_intelligence.nasa_london_imagery("2026-11-18") == result
    assert len(calls) == 1
    for day in ("2099-01-01", "../../private", "2026-02-30"):
        try:
            third_eye_intelligence.nasa_london_imagery(day)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid NASA imagery day accepted")


def test_new_public_data_sources_fail_closed_without_inventing_live_data(monkeypatch):
    monkeypatch.setattr(third_eye_intelligence, "_THIRD_EYE_SOURCE_CACHE", {})
    def unavailable(*args, **kwargs):
        raise TimeoutError("provider not reachable")
    monkeypatch.setattr(third_eye_intelligence, "_fixed_download", unavailable)
    assert third_eye_intelligence.london_aircraft()["live_claim_allowed"] is False
    assert third_eye_intelligence.iss_position()["live_claim_allowed"] is False
    assert third_eye_intelligence.iss_orbital_elements()["position_propagated"] is False
    assert third_eye_intelligence.nasa_london_imagery("2026-11-18") is None


def test_new_air_and_space_routes_are_founder_private_and_anonymous_denied(client, monkeypatch):
    endpoints = (
        "alignment.smi_third_eye_air_london",
        "alignment.smi_third_eye_space_iss",
        "alignment.smi_third_eye_space_orbit",
        "alignment.smi_third_eye_space_imagery",
    )
    for endpoint in endpoints:
        view = app_module.app.view_functions[endpoint]
        assert view._oap_login_required is True
        assert view._oap_founder_only is True
        assert view._oap_api is True
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    for path in (
        "/mission/smi/third-eye/air/london",
        "/mission/smi/third-eye/space/iss",
        "/mission/smi/third-eye/space/orbit",
        "/mission/smi/third-eye/space/imagery?day=2026-11-18",
    ):
        response = client.get(path)
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "authentication_required"


def test_third_eye_source_controls_are_wired_to_existing_views():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "mission_control"
    template = (root / "templates" / "ollama_chat.html").read_text(encoding="utf-8")
    script = (root / "static" / "smi_third_eye.js").read_text(encoding="utf-8")
    for key in (
        "thirdEyeAirLondonUrl:", "thirdEyeSpaceIssUrl:",
        "thirdEyeSpaceOrbitUrl:", "thirdEyeSpaceImageryUrl:",
    ):
        assert key in template
        assert "config." + key[:-1] in script
    assert "function checkLondonAir()" in script
    assert "function checkSpaceSource(kind)" in script
    assert "function showNasaLondonImage(day)" in script
    assert "NASA GIBS" in script
    assert "capture" in script or "acquisition" in script
    assert "getCurrentPosition" not in script
    assert "setInterval" not in script
