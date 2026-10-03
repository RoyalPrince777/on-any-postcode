from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "mission_control" / "templates" / "linkup.html").read_text(encoding="utf-8")
NETWORK = (ROOT / "static" / "linkup_network.js").read_text(encoding="utf-8")
INSTALL = (ROOT / "static" / "oap-os.js").read_text(encoding="utf-8")
WORKER = (ROOT / "static" / "oap-os-sw.js").read_text(encoding="utf-8")
OFFLINE = (ROOT / "static" / "oap-os-offline.html").read_text(encoding="utf-8")


def test_linkup_exposes_install_and_live_network_status():
    assert "data-oap-install hidden" in TEMPLATE
    assert "Install Link Up" in TEMPLATE
    assert "data-oap-install-status" in TEMPLATE
    assert "data-oap-linkup-network-status" in TEMPLATE
    assert "linkup_network.js" in TEMPLATE
    assert "⚙ My Controls" in TEMPLATE
    assert "⚙ Settings" not in TEMPLATE


def test_linkup_network_guard_never_queues_private_actions_offline():
    assert "navigator.onLine" in NETWORK
    assert "Offline · private actions paused until you reconnect" in NETWORK
    assert "[data-oap-link-composer]" in NETWORK
    assert "[data-oap-call-control]" in NETWORK
    assert "[data-oap-voice-control]" in NETWORK
    assert "[data-oap-share-spot-control]" in NETWORK
    assert "[data-oap-live-spot-control]" in NETWORK
    assert "event.preventDefault()" in NETWORK
    assert "indexedDB" not in NETWORK
    assert "localStorage" not in NETWORK
    assert "sessionStorage" not in NETWORK
    assert "queue" not in NETWORK.casefold()


def test_installer_uses_linkup_name_on_linkup_route():
    assert 'location.pathname === "/linkup"' in INSTALL
    assert 'location.pathname.startsWith("/linkup/")' in INSTALL
    assert '? "Link Up"' in INSTALL
    assert "${productName} is ready to install" in INSTALL
    assert "${productName} is installed" in INSTALL


def test_offline_shell_is_linkup_aware_but_contains_no_private_content():
    assert 'location.pathname === "/linkup"' in OFFLINE
    assert "Link Up is offline" in OFFLINE
    assert "Private messages, calls, Voice, presence and location stay online-only" in OFFLINE
    assert 'retry.href = "/linkup"' in OFFLINE
    assert 'window.addEventListener("online", () => location.reload())' in OFFLINE
    assert "<form" not in OFFLINE.casefold()


def test_service_worker_remains_network_first_for_linkup_navigation():
    assert 'const CACHE_VERSION = "oap-os-public-v1.1";' in WORKER
    assert 'if (request.mode === "navigate")' in WORKER
    assert 'fetch(request).catch(() => caches.match("/offline"))' in WORKER
    assert "cache.put" not in WORKER
    public_shell = WORKER.split("const PRIVATE_PREFIXES", 1)[0]
    assert '"/linkup"' not in public_shell
