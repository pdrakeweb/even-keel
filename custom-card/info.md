# EvenKeel Boat Card

A Lovelace custom card showing a top-down sailboat diagram with severity-colored zones, animated power flow, and tap-to-drill into category detail views.

Built for the [EvenKeel](https://github.com/pdrakeweb/even-keel) DIY sailboat-monitoring system, but works with any HA setup that provides:

- 8 rollup status sensors (`sensor.boat_<category>_status`) with state ∈ {`ok`, `warning`, `critical`} and a `headline` attribute
- A primary alert sensor (`sensor.boat_primary_alert`) returning the highest-priority issue in plain English
- Optional power-flow indicators (shore / generator / solar / battery V/A)
- Optional vital signs (AIS count, wind speed, anchor armed)

## Install via HACS

1. HACS → Frontend → ⋮ menu → Custom repositories → Add `https://github.com/pdrakeweb/even-keel`, category **Lovelace**.
2. Find "EvenKeel Boat Card" in the Frontend list and install.
3. Refresh your browser. The card type is `custom:evenkeel-boat-card`.

## Quick config

```yaml
type: custom:evenkeel-boat-card
boat_name: My Sailboat
overall_status: sensor.boat_primary_alert
zones:
  bilge:
    rollup: sensor.boat_bilge_status
    navigate: /lovelace/boat/bilge
  engine:
    rollup: sensor.boat_engine_tanks_status
    navigate: /lovelace/boat/engine
  # … cabin, v_berth, head, galley, lazarette, nav …
power_flow:
  shore: binary_sensor.boat_shore_power
  battery_v: sensor.boat_house_battery_v
  battery_a: sensor.boat_house_battery_a
footer_vitals:
  - sensor.boat_ais_targets_in_range
  - sensor.boat_apparent_wind_speed
  - binary_sensor.boat_anchor_armed
  - sensor.boat_house_battery_v
```

See the [full docs](https://github.com/pdrakeweb/even-keel/blob/master/custom-card/README.md) for the complete config schema.

## Themes

The card respects your active HA theme's `--evenkeel-ok`, `--evenkeel-warn`, `--evenkeel-crit` variables. Two themes ship with EvenKeel:

- **evenkeel-minimal** — iOS Apple-Weather aesthetic (default)
- **evenkeel-marine** — Brass + navy + walnut, B&G/Raymarine-inspired

## License

Apache-2.0.
