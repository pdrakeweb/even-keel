# EvenKeel

[![Simulator tests](https://github.com/pdrakeweb/even-keel/actions/workflows/simulator-tests.yml/badge.svg)](https://github.com/pdrakeweb/even-keel/actions/workflows/simulator-tests.yml)
[![Custom card](https://github.com/pdrakeweb/even-keel/actions/workflows/custom-card.yml/badge.svg)](https://github.com/pdrakeweb/even-keel/actions/workflows/custom-card.yml)
[![HA config](https://github.com/pdrakeweb/even-keel/actions/workflows/ha-config.yml/badge.svg)](https://github.com/pdrakeweb/even-keel/actions/workflows/ha-config.yml)

A DIY sailboat monitoring, AIS, and alerting system for a Hunter 41DS on Lake Erie.

Built around a single ESP32-S3 on the boat, a Home Assistant instance at home, and a zero-subscription infrastructure — no cloud dependencies, no third-party integrations required, no ongoing costs.

## Status

**Iteration 1 complete.** Foundations in place:

- ✅ Boat telemetry **simulator** (Python) with 9 scenarios — covered by 164 pytest tests
- ✅ **Home Assistant** configuration: 3 dashboards, 9 rollup template sensors, 2 themes (Modern Minimal + Marine Classic), Captain's Glance primary-alert engine
- ✅ **Custom Lovelace card** (`evenkeel-boat-card`) — HACS-installable, Lit + TypeScript + Vite, top-down sailboat diagram with severity overlays + animated power flow + tap-to-drill navigation, 73 unit tests
- ✅ **CI**: GitHub Actions for pytest (Python 3.10/3.11/3.12), card build (Node 20/22), HA config check, Wokwi firmware skeleton
- ✅ **Local dev stack**: docker-compose runs mosquitto + HA + simulator end-to-end

**Iteration 2 in flight:**
- ESP32-S3 ESPHome firmware (`firmware/boat-mon.yaml`) + Wokwi simulator config
- First Gherkin AIS-TCP-bridge scenario passing in CI under virtual mode
- Custom card SVG enhancements (proper Hunter 41DS profile, click→drill)

## Quickstart — develop without hardware

```bash
git clone https://github.com/pdrakeweb/even-keel.git
cd even-keel
cp home-assistant/secrets.yaml.example home-assistant/secrets.yaml
docker compose up -d
# Open http://localhost:8123, log in, navigate to "How's My Boat",
# Dev tab → toggle "Use simulated boat data" → pick a scenario.
```

See [`docs/ui-dev-quickstart.md`](docs/ui-dev-quickstart.md) for the full walkthrough.

## Install the custom Lovelace card

Via **HACS**:

1. HACS → Frontend → ⋮ → Custom repositories.
2. Add `https://github.com/pdrakeweb/even-keel`, category **Lovelace**.
3. Find "EvenKeel Boat Card" and install.
4. Refresh browser; card type is `custom:evenkeel-boat-card`.

Or build from source:

```bash
cd custom-card
npm install
npm run build
cp dist/evenkeel-boat-card.js ../home-assistant/www/
```

Then add the resource in HA: Settings → Dashboards → Resources → `+` → URL `/local/evenkeel-boat-card.js`, type **JavaScript Module**.

## Run the tests

```bash
# Python simulator — 164 tests
cd simulator
pip install -e '.[dev]'
pytest

# Custom card — 73 tests (TypeScript + happy-dom)
cd ../custom-card
npm install
npm run lint   # tsc --noEmit
npm run test   # vitest
npm run build  # vite → dist/evenkeel-boat-card.js
```

## Repo layout

```
research/           original design docs (v1.0 + continuation brief)
planning/           research reports + synthesis (architecture, roadmap, custom-card-research)
firmware/           ESPHome YAML — boat node + Tier 1 dashboard head (Iteration 2)
tests/              pytest-bdd test harness (virtual / HIL / live modes — Iteration 2)
hil-rig/            bench hardware-in-the-loop stimulator
home-assistant/     HA configuration: dashboards, themes, automations, packages, README
simulator/          boat telemetry simulator + 164 pytest tests; Docker-built service
custom-card/        HACS-installable Lovelace card: Lit + TS + Vite, 73 vitest tests
relay/              optional aisstream.io forwarder
docs/               runbooks, photos, install guides — start at ui-dev-quickstart.md
tools/              one-off scripts (MQTT replay, AIS capture, cert rotation)
docker-compose.yml  local dev stack (mosquitto + HA + simulator)
.github/workflows/  CI: simulator pytest, custom-card build, HA config check, Wokwi
.env.example        template for WOKWI_CLI_TOKEN, HA_TOKEN, Pushover keys
```

## Documentation map

| Topic | File |
|---|---|
| **Project overview** | This file |
| **Plan & roadmap** | [`planning/README.md`](planning/README.md) → [`planning/roadmap.md`](planning/roadmap.md) |
| **System architecture** | [`planning/architecture.md`](planning/architecture.md) |
| **Hardware bill of materials** | [`planning/hardware-deep-dive.md`](planning/hardware-deep-dive.md) |
| **Custom card design** | [`planning/custom-card-research.md`](planning/custom-card-research.md) |
| **NMEA 2000 integration** | [`planning/nmea2000-integration.md`](planning/nmea2000-integration.md) |
| **Sensor expansion (5–30+ sensors)** | [`planning/sensor-expansion.md`](planning/sensor-expansion.md) |
| **Open questions** | [`planning/open-questions.md`](planning/open-questions.md) |
| **TDD / test architecture** | [`planning/tdd-architecture.md`](planning/tdd-architecture.md) |
| **Local dev quickstart** | [`docs/ui-dev-quickstart.md`](docs/ui-dev-quickstart.md) |
| **HA configuration** | [`home-assistant/README.md`](home-assistant/README.md) |
| **Simulator service** | [`simulator/README.md`](simulator/README.md) |
| **Custom card plugin** | [`custom-card/README.md`](custom-card/README.md) |
| **HIL bench rig** | [`hil-rig/README.md`](hil-rig/README.md) |

## Design principles

1. **Reliability under marine conditions.** Fail-open severity (a missing sensor never paints the dashboard red), watchdogs, OTA recovery.
2. **No subscription dependencies.** Every required feature works on Pete's own hardware. Optional integrations (Pushover, aisstream.io) are explicitly opt-in.
3. **ESPHome YAML-first.** Minimal custom firmware. The simulator and tests speak the same MQTT topics the real ESP32 will.
4. **Commercial, replaceable parts.** No custom PCBs. STEMMA QT / Qwiic plug-together for sensors.
5. **Phased.** Each phase ships working end-to-end functionality. Pete can stop at any phase and have a useful system.
6. **Test-driven.** Natural-language Gherkin scenarios + pytest-bdd, runnable against simulated boat or real hardware via the same step definitions.

## Current dashboard at a glance

The HA "How's My Boat" dashboard surfaces 8 boat-system categories as colored buttons (green / orange / red), with a Captain's Glance headline at the top describing the single most-urgent issue in plain English ("Water in the bilge — Pete needs to check now"). Tap any category for drill-down detail.

The custom card layers on top: a top-down Hunter 41DS diagram where each compartment lights up by severity, with an animated shore→battery power-flow line.

## License

Apache-2.0.
