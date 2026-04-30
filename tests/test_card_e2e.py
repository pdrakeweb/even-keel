"""Playwright end-to-end tests for the EvenKeel boat card.

Loads the production bundle from `custom-card/dist/` in a real
Chromium and asserts the rendered shadow DOM behaves the way HACS
users will see it. Complements the happy-dom unit tests in
`custom-card/test/` — those test pure functions and the Lit element
in isolation; these test the bundle end-to-end against a real
browser's SVG namespace, CSS animation, and event dispatch.

The harness is served via a session-scoped http.server because
Chromium blocks ES-module imports on `file://` URLs by default.

These tests are skipped on Windows: tests/conftest.py forces a
SelectorEventLoop for aiomqtt, but Playwright on Windows requires
the ProactorEventLoop for subprocess support — the two are mutually
exclusive in a single pytest process. CI runs on Linux.
"""
from __future__ import annotations

import http.server
import json
import pathlib
import socketserver
import sys
import threading
from typing import Iterator

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Playwright + aiomqtt event-loop conflict on Windows; runs in CI",
)


_REPO_ROOT = pathlib.Path(__file__).parent.parent
_HARNESS_PATH = "tests/e2e/index.html"


@pytest.fixture(scope="session")
def http_server() -> Iterator[str]:
    """Serve the repo root over HTTP so Chromium can fetch ES modules.

    Picks an ephemeral port. SimpleHTTPRequestHandler serves files
    relative to the directory passed via the directory= kwarg. Returns
    the base URL ("http://127.0.0.1:<port>"). Tests append the harness
    path.
    """
    handler_factory = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(_REPO_ROOT), **kw
    )
    server = socketserver.TCPServer(("127.0.0.1", 0), handler_factory)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def loaded(page, http_server: str):
    """Navigate to the harness; returns the Playwright page once ready."""
    page.goto(f"{http_server}/{_HARNESS_PATH}")
    page.wait_for_selector("body[data-ready='1']", timeout=10000)
    return page


def test_custom_element_registers(loaded) -> None:
    """The bundle should self-register `evenkeel-boat-card` on import."""
    is_registered = loaded.evaluate(
        "() => Boolean(customElements.get('evenkeel-boat-card'))"
    )
    assert is_registered is True


def test_card_picker_metadata(loaded) -> None:
    """HA's GUI editor scans `window.customCards`; we must appear there."""
    entry = loaded.evaluate(
        "() => (window.customCards || []).find(c => c.type === 'evenkeel-boat-card')"
    )
    assert entry is not None
    assert entry["name"] == "EvenKeel Boat Card"


def test_renders_minimal_config_with_no_hass(loaded) -> None:
    """Config-only mount renders the card with the fallback headline."""
    loaded.evaluate(
        "() => window.__mount({type: 'custom:evenkeel-boat-card', boat_name: 'Test Vessel'})"
    )
    loaded.wait_for_function("() => window.__readyState()")
    html = loaded.evaluate("async () => (await window.__readyState()).innerHTML")
    assert "Test Vessel" in html
    assert "All good" in html  # default fallback headline
    assert "<svg" in html


def test_critical_severity_paints_glance(loaded) -> None:
    """An overall_status entity in 'critical' state colors the headline."""
    hass = {
        "states": {
            "sensor.boat_primary_alert": {
                "state": "critical",
                "attributes": {
                    "headline": "Water in the bilge - Pete needs to check now",
                },
            },
        },
    }
    loaded.evaluate(
        "(hass) => window.__mount({type:'custom:evenkeel-boat-card', overall_status:'sensor.boat_primary_alert'}, hass)",
        hass,
    )
    loaded.wait_for_function("() => window.__readyState()")
    html = loaded.evaluate("async () => (await window.__readyState()).innerHTML")
    assert "Water in the bilge" in html
    # Severity class is applied to the glance row
    assert "severity-critical" in html


def test_zone_renders_with_severity_class(loaded) -> None:
    """A configured zone whose rollup is 'warning' picks up severity-warning."""
    hass = {
        "states": {
            "sensor.boat_engine_status": {
                "state": "warning",
                "attributes": {"headline": "Engine coolant high"},
            },
        },
    }
    config = {
        "type": "custom:evenkeel-boat-card",
        "zones": {"engine_bay": {"rollup": "sensor.boat_engine_status"}},
    }
    loaded.evaluate(
        "(args) => window.__mount(args.config, args.hass)",
        {"config": config, "hass": hass},
    )
    loaded.wait_for_function("() => window.__readyState()")
    classes = loaded.evaluate("""
        async () => {
          const root = await window.__readyState();
          const zone = root.querySelector('[data-zone="engine_bay"]');
          return zone ? zone.getAttribute('class') : null;
        }
    """)
    assert classes is not None
    assert "severity-warning" in classes


def test_no_runtime_errors_on_full_config(loaded) -> None:
    """Mounting with a fully populated config doesn't throw."""
    hass = {
        "states": {
            "sensor.boat_primary_alert": {"state": "ok", "attributes": {"headline": "All good"}},
            "sensor.boat_bilge_status": {"state": "ok", "attributes": {}},
            "sensor.boat_engine_status": {"state": "ok", "attributes": {}},
            "sensor.boat_house_battery_v": {"state": "12.7", "attributes": {"unit_of_measurement": "V"}},
            "binary_sensor.boat_shore_power": {"state": "on", "attributes": {}},
        },
    }
    config = {
        "type": "custom:evenkeel-boat-card",
        "boat_name": "Hunter 41DS",
        "overall_status": "sensor.boat_primary_alert",
        "zones": {
            "bilge": {"rollup": "sensor.boat_bilge_status"},
            "engine_bay": {"rollup": "sensor.boat_engine_status"},
        },
        "power_flow": {
            "shore": "binary_sensor.boat_shore_power",
            "battery_v": "sensor.boat_house_battery_v",
        },
        "footer_vitals": ["sensor.boat_house_battery_v"],
    }
    loaded.evaluate(
        "(args) => window.__mount(args.config, args.hass)",
        {"config": config, "hass": hass},
    )
    loaded.wait_for_function("() => window.__readyState()")
    err = loaded.evaluate(
        "() => document.getElementById('error').hidden ? null : document.getElementById('error').textContent"
    )
    assert err is None, f"runtime error: {err}"
