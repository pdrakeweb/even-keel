"""Playwright end-to-end tests for the EvenKeel boat card.

Loads the production bundle from `custom-card/dist/` in a real
Chromium and asserts the rendered shadow DOM behaves the way HACS
users will see it. Complements the happy-dom unit tests in
`custom-card/test/` — those test pure functions and the Lit element
in isolation; these test the bundle end-to-end against a real
browser's SVG namespace, CSS animation, and event dispatch.

Loaded via `file://` so no test server is needed. Fixtures from
`pytest-playwright` provide `page` and `browser`.

These tests are skipped on Windows: tests/conftest.py forces a
SelectorEventLoop for aiomqtt, but Playwright on Windows requires
the ProactorEventLoop for subprocess support — the two are mutually
exclusive in a single pytest process. CI runs on Linux and works
fine; develop these tests under WSL or rely on CI feedback.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Playwright + aiomqtt event-loop conflict on Windows; runs in CI",
)

# Resolve the harness URL once. tests/ is the rootdir; tests/e2e/index.html
# imports the bundle via a relative path the browser fetches via file://.
_HARNESS = pathlib.Path(__file__).parent / "e2e" / "index.html"
_HARNESS_URL = _HARNESS.resolve().as_uri()


def _make_hass(states: dict) -> str:
    """Serialize a minimal hass-shaped object as a JS expression."""
    return json.dumps({"states": states})


@pytest.fixture
def loaded(page):
    """Navigate to the harness; returns the Playwright page once ready."""
    page.goto(_HARNESS_URL)
    page.wait_for_selector("body[data-ready='1']", timeout=5000)
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
    hass = _make_hass({
        "sensor.boat_primary_alert": {
            "state": "critical",
            "attributes": {
                "headline": "Water in the bilge — Pete needs to check now",
            },
        },
    })
    loaded.evaluate(
        f"(hass) => window.__mount({{type:'custom:evenkeel-boat-card', overall_status:'sensor.boat_primary_alert'}}, hass)",
        json.loads(hass),
    )
    loaded.wait_for_function("() => window.__readyState()")
    html = loaded.evaluate("async () => (await window.__readyState()).innerHTML")
    assert "Water in the bilge" in html
    # Severity class is applied to the glance row
    assert "severity-critical" in html


def test_zone_renders_with_severity_class(loaded) -> None:
    """A configured zone whose rollup is 'warning' picks up severity-warning."""
    hass = _make_hass({
        "sensor.boat_engine_status": {
            "state": "warning",
            "attributes": {"headline": "Engine coolant high"},
        },
    })
    config = {
        "type": "custom:evenkeel-boat-card",
        "zones": {"engine_bay": {"rollup": "sensor.boat_engine_status"}},
    }
    loaded.evaluate(
        "(args) => window.__mount(args.config, args.hass)",
        {"config": config, "hass": json.loads(hass)},
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
    hass = _make_hass({
        "sensor.boat_primary_alert": {"state": "ok", "attributes": {"headline": "All good"}},
        "sensor.boat_bilge_status": {"state": "ok", "attributes": {}},
        "sensor.boat_engine_status": {"state": "ok", "attributes": {}},
        "sensor.boat_house_battery_v": {"state": "12.7", "attributes": {"unit_of_measurement": "V"}},
        "binary_sensor.boat_shore_power": {"state": "on", "attributes": {}},
    })
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
        {"config": config, "hass": json.loads(hass)},
    )
    loaded.wait_for_function("() => window.__readyState()")
    err = loaded.evaluate(
        "() => document.getElementById('error').hidden ? null : document.getElementById('error').textContent"
    )
    assert err is None, f"runtime error: {err}"
