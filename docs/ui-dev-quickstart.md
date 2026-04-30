# EvenKeel UI Development Quickstart

Develop and iterate on the Home Assistant dashboards (Modern Minimal, Marine Classic, Pete's Power) **without any boat hardware**.

## Prerequisites

- Docker Desktop / Docker Engine + Compose v2
- ~1 GB free disk for HA + Mosquitto images
- Pete's existing local dev tools (any code editor)

## Bring up the stack

```bash
# from repo root
cp home-assistant/secrets.yaml.example home-assistant/secrets.yaml
docker compose up -d
```

This starts three containers:
- `evenkeel-mosquitto` (MQTT broker on `localhost:1883`)
- `evenkeel-homeassistant` (HA on `http://localhost:8123`)
- `evenkeel-simulator` (boat-data publisher, **starts paused**)

First HA boot takes ~60 seconds. Watch with `docker compose logs -f homeassistant`.

## Onboard HA

1. Browse to <http://localhost:8123>.
2. Create the admin account (any name — local dev only).
3. HA will detect the local `mosquitto` broker via the configuration.yaml; you should see "MQTT" appear in Settings → Devices.
4. Open the **How's My Boat** dashboard from the sidebar.

The dashboard will be empty initially — the simulator is paused.

## Turn on the simulator

In the dashboard, switch to the **Dev** tab. You'll see a card titled "Switch between simulator and real hardware":

1. Toggle **Use simulated boat data** → ON.
2. Choose a scenario in the **Scenario** dropdown (start with `normal`).
3. Switch back to the **Boat** tab — within ~10 seconds, sensor entities populate and tiles show live data.

Scenarios you can flip between for visual testing:

| Scenario | What you'll see |
|---|---|
| `normal` | Calm green dashboard. House battery ~12.7 V, shore power, all temps in band. |
| `low_battery` | House V drops 12.6 → 11.7 V over 10 min, generator kicks on, slow recovery. |
| `bilge_wet` | Bilge tile turns red between t=30s and t=120s, then back to dry. |
| `shore_lost` | Shore plug icon goes off, source switches to "battery", V drops slowly. |
| `gen_running` | Generator on, charging current visible, recovery curve. |
| `anchor_drag` | Position drifts away from anchor; map and SOG update. |
| `underway` | At sea: position moves, SOG ~5 kt, AIS targets fluctuate. |
| `all_critical` | Everything red at once — for stress-testing severity styling. |
| `cycle` | Rotates all scenarios every 90s — perfect for demos and screenshot baselines. |

## How the swap works

```
input_boolean.use_simulator (HA UI)
  → automation publishes  boat/control/simulator/run = on|off  (retained MQTT)
    → simulator service reads it, starts/stops publishing
      → simulator publishes to  boat/hunter41/...  (canonical topics)
        → HA's MQTT integration auto-discovers entities
          → dashboards render
```

The dashboards always read `boat/hunter41/...` — they have no idea whether the publisher is the simulator or a real ESP32. **That's the abstraction.** When you eventually plug in real hardware:

1. Toggle the simulator OFF.
2. Real boat starts publishing to the same topics.
3. Dashboards reflect real data without any config changes.

You can also run them simultaneously — last writer wins, with retained messages serving stale snapshots in between.

## Editing dashboards

All Lovelace YAML lives in `home-assistant/lovelace/`:

| File | What |
|---|---|
| `kellys-card.yaml` | Modern Minimal default — Kelly's view |
| `kellys-card-marine.yaml` | Marine Classic alternate — same data, brass + navy theme |
| `petes-power.yaml` | Data-Dense — Pete's diagnostic view |

Edit any YAML file → save → in HA, hit Settings → Server Controls → "Reload Lovelace" (or just refresh the dashboard page).

Themes live in `home-assistant/themes/`:

- `evenkeel-minimal.yaml` — Modern Minimal
- `evenkeel-marine.yaml` — Marine Classic

Switch active theme per-user under your HA profile, or per-dashboard via the `theme:` key at the top of the lovelace YAML.

## Editing the simulator

The simulator is a Python package at `simulator/`:

- `src/evenkeel_sim/scenarios.py` — scenario definitions (where the data shapes live)
- `src/evenkeel_sim/sensors.py` — canonical sensor model + topic mapping
- `src/evenkeel_sim/discovery.py` — HA MQTT discovery payloads
- `src/evenkeel_sim/publisher.py` — MQTT loop + control listener

To rebuild after a change:

```bash
docker compose build boat-simulator
docker compose up -d boat-simulator
```

For a faster inner loop, run the simulator outside Docker:

```bash
cd simulator
python -m venv .venv && source .venv/bin/activate   # or .venv/Scripts/activate on Windows
pip install -e .
python -m evenkeel_sim --broker localhost --scenario cycle
```

## Tearing down

```bash
docker compose down              # stops containers, keeps volumes
docker compose down -v           # also wipes mosquitto + HA volumes (full reset)
```

## Working with real hardware later

When the actual boat ESP32 firmware is flashed and online:

1. Point your HA at the boat's MQTT broker (edit `home-assistant/secrets.yaml`'s `mqtt_broker` to the boat broker hostname or WG IP).
2. Restart HA: `docker compose restart homeassistant`.
3. In the Dev tab, toggle **Use simulated boat data** OFF. The real boat takes over the same topic tree.
4. (Optional) Re-enable the simulator any time for demos — it doesn't hurt anything; it republishes alongside real data, and HA simply shows whichever topic was retained most recently.

That's the whole abstraction: **one set of MQTT topics, two interchangeable publishers, single setting to swap.**

## Troubleshooting

| Symptom | Fix |
|---|---|
| HA dashboard shows "Entity not available" | Toggle simulator ON; wait 10s for first publish + HA discovery |
| Simulator container restarts in a loop | Check `docker compose logs boat-simulator` — usually a Mosquitto reachability issue |
| Tiles don't change color when scenario changes | Clear browser cache; HA's MQTT discovery is retained, so old entity defs may be cached |
| `mosquitto_sub -h localhost -t 'boat/#' -v` shows no traffic | Simulator is paused. Check `boat/control/simulator/run` value — should be `on` |
| Themes look broken | Settings → Profile → Theme → choose `evenkeel-minimal` or `evenkeel-marine` |

## See also

- [`../simulator/README.md`](../simulator/README.md) — simulator details, scenario authoring
- [`../home-assistant/packages/boat-controls.yaml`](../home-assistant/packages/boat-controls.yaml) — the toggle automation
- [`../planning/architecture.md §2.7`](../planning/architecture.md) — dashboard surfaces & themes
- [`../planning/mockups/`](../planning/mockups/) — visual references the implementations match
