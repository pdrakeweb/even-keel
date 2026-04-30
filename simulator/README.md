# EvenKeel Boat Simulator

A Python service that publishes realistic boat telemetry to MQTT — used for **UI development without hardware**, integration testing, and demo mode.

## Why it exists

EvenKeel's UI work (HA Lovelace dashboards, ESPHome web_server, eventual Tier 1 LVGL panel) shouldn't wait for the actual ESP32 hardware to be installed on a boat. This simulator publishes to the **canonical MQTT topics** (`boat/hunter41/...`) that the real boat will use, so dashboards and automations can be developed and visually iterated against live, varying data.

## Runtime toggle (the "setting")

The simulator runs only when Home Assistant's `input_boolean.use_simulator` is ON. Flipping that toggle:

- **ON**: a control message is sent on `boat/control/simulator/run = on`. Simulator starts publishing to `boat/hunter41/...` topics. Real boat (if connected) is overridden by the simulator's higher-frequency retained messages.
- **OFF**: simulator stops publishing. If real hardware is online, its data takes over the same topics.

The dashboard reads `boat/hunter41/...` regardless. **No template-sensor swap, no entity renaming, no config drift.** One topic tree, two possible publishers.

This satisfies the "swap at runtime between simulated and real hardware via a setting" requirement.

## Scenarios

The simulator publishes data shaped by a current **scenario**. Set via `input_select.simulator_scenario` in HA, which publishes to `boat/control/simulator/scenario`.

| Scenario | Behavior |
|---|---|
| `normal` (default) | At slip, shore power, batteries 12.6–12.8 V, all temps in band, bilge dry. Random walk within healthy ranges. |
| `low_battery` | House battery sags from 12.6 V to 11.7 V over 15 min, generator kicks on, recovery cycle. |
| `bilge_wet` | Float switch goes wet for 90 s, then dries out. |
| `shore_lost` | Shore power disconnects, system on battery, voltage drops slowly. |
| `gen_running` | Generator is on, charging house bank back from 11.9 V. |
| `anchor_drag` | GPS track drifts 60 m from armed anchor point over 3 min. |
| `underway` | At sea: shore off, slow battery discharge, boat motion (lat/lon ticks), AIS targets pop in/out. |
| `all_critical` | Everything red at once — for stress-testing the dashboard. |
| `cycle` | Rotates through all scenarios every 90 seconds — perfect for demos and visual regression baselines. |

Scenarios are defined declaratively in `config/scenarios.yaml` so non-programmers can edit them. Each scenario specifies sensor target values, jitter ranges, and transition rules.

## Topics published

The simulator publishes the full canonical EvenKeel topic tree, matching `architecture.md §2.7` and `infrastructure.md §3`:

```
boat/hunter41/status/online                         (retained, LWT)
boat/hunter41/power/shore                           (0/1)
boat/hunter41/power/generator                       (0/1)
boat/hunter41/power/source                          ("shore"|"generator"|"battery")
boat/hunter41/power/battery/house/v                 (V)
boat/hunter41/power/battery/house/a                 (A)
boat/hunter41/power/battery/house/soc               (% — populated only in scenarios w/ Victron)
boat/hunter41/power/battery/start/v                 (V)
boat/hunter41/temp/cabin                            (°C)
boat/hunter41/temp/engine_compartment               (°C)
boat/hunter41/temp/refrigerator                     (°C)
boat/hunter41/cabin/humidity                        (%RH)
boat/hunter41/cabin/pressure                        (hPa)
boat/hunter41/bilge/water_detected                  (0/1)
boat/hunter41/health/rssi                           (dBm)
boat/hunter41/health/uptime_s                       (s)
boat/hunter41/location/lat                          (°)
boat/hunter41/location/lon                          (°)
boat/hunter41/location/sog                          (kt)
boat/hunter41/location/cog                          (°)
boat/hunter41/sim/scenario                          (current scenario name, retained)
boat/hunter41/sim/active                            (1 = simulator publishing, retained)
```

Plus MQTT discovery messages under `homeassistant/...` so HA auto-creates entities on first run.

## Quickstart

### Local Python dev

```bash
cd simulator
python -m venv .venv && source .venv/bin/activate
pip install -e .
export MQTT_BROKER=localhost MQTT_PORT=1883
export INITIAL_SCENARIO=cycle
python -m evenkeel_sim
```

### Docker (recommended)

```bash
# from repo root
docker compose up boat-simulator mosquitto homeassistant
# Open http://localhost:8123, navigate to "How's My Boat" — it'll be live within ~10 seconds
```

### Standalone in production HA

Once the real boat hardware is online, you may still want the simulator available — for demo days, dashboard tweaks, regression testing. Install as a Home Assistant Add-on (`docker/ha-addon/`) and toggle from the HA UI.

## Architecture

```
┌──────────────────────────────────────────────┐
│ Home Assistant                               │
│  • input_boolean.use_simulator               │
│  • input_select.simulator_scenario           │
│  • Automations publish control topics        │
└────────────┬─────────────────────────────────┘
             │ MQTT control plane
             │ boat/control/simulator/run, /scenario
             ▼
┌──────────────────────────────────────────────┐
│ Boat Simulator (this service)                │
│  • Reads control topics                      │
│  • Loads scenario from config/scenarios.yaml │
│  • Generates realistic randomized values     │
│  • Publishes to boat/hunter41/... at 1 Hz    │
└────────────┬─────────────────────────────────┘
             │ MQTT data plane
             │ boat/hunter41/...
             ▼
┌──────────────────────────────────────────────┐
│ Mosquitto                                    │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────┐
│ Home Assistant (subscriber side)             │
│  Dashboards · automations · recorder         │
└──────────────────────────────────────────────┘
```

## Layout

```
simulator/
  README.md
  pyproject.toml
  Dockerfile
  src/
    evenkeel_sim/
      __init__.py
      __main__.py          # entry point: python -m evenkeel_sim
      sensors.py           # SensorSnapshot dataclass + canonical fields
      scenarios.py         # scenario engine (loaded from yaml)
      publisher.py         # MQTT client + discovery + publish loop
      control.py           # listens for input_boolean / input_select changes
      generators.py        # randomness + drift + transient helpers
      cli.py               # argparse + env handling
  config/
    scenarios.yaml         # editable scenario definitions
  tests/
    test_scenarios.py
    test_publisher.py
```

## Extending

To add a new scenario:

1. Append to `config/scenarios.yaml`:
   ```yaml
   - name: my_scenario
     description: "What it tests"
     duration_s: 120
     sensors:
       house_v: { target: 12.4, jitter: 0.05 }
       bilge_wet: { value: false }
       # … any canonical sensor field
     events:
       - at_s: 60
         set:
           bilge_wet: true
   ```
2. Add the name to `input_select.simulator_scenario` in `home-assistant/packages/boat-controls.yaml`.
3. Restart the simulator. It hot-reloads scenarios on SIGHUP.

To add a new sensor field:

1. Add to `SensorSnapshot` dataclass in `sensors.py`.
2. Add to `_publish_telemetry` in `publisher.py`.
3. Add MQTT discovery payload in `discovery.py`.
4. Add scenario default in `scenarios.yaml`.

The library is intentionally a thin "stub" generator. It does not simulate physics or marine dynamics. Its purpose is to feed dashboards plausible-looking data, including alarm states, so you can develop UI without hardware.

## See also

- [`../home-assistant/packages/boat-controls.yaml`](../home-assistant/packages/boat-controls.yaml) — HA-side toggles and automations
- [`../planning/architecture.md §2.7`](../planning/architecture.md) — dashboard surfaces and themes
- [`../planning/tdd-architecture.md §B`](../planning/tdd-architecture.md) — relationship to the test harness (this simulator is the "Virtual Adapter" in dashboard-only mode)
