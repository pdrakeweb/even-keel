# EvenKeel Boat Card

Lovelace custom card for the [EvenKeel](https://github.com/pdrakeweb/even-keel) DIY sailboat-monitoring system. Renders a top-down sailboat diagram with severity-colored zones, animated power flow, a Captain's Glance headline, and tap-to-drill navigation.

> **Status:** v0.1 scaffold. Builds, validates config, renders the Hunter 41DS profile + zones. Power-flow ant animation works. Full visual regression / multi-boat support is post-v1.

## Layout

```
┌──── Hunter 41DS — Water in the bilge — Pete needs to check now ────┐
│                                                                     │
│   ┌──────────────────────────────────────────────┐                  │
│   │ LAZ      COCKPIT    ENGINE GALLEY HEAD V-BERTH FOREPEAK│        │
│   │                              NAV    SALON           │            │
│   │ ════════════ bilge strip ══════════════════════════ │            │
│   └──────────────────────────────────────────────┘                  │
│                                                                     │
│  SHORE ━━━━━━━━━━━━━━━▶ BATT 12.6 V                                 │
│                                                                     │
│  AIS  ⛵ wind  🌬 anchor  ⚓ batt  🔋                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Install via HACS

1. HACS → Frontend → ⋮ → Custom repositories → Add `https://github.com/pdrakeweb/even-keel`, category **Lovelace**.
2. Find "EvenKeel Boat Card" in the Frontend list and install.
3. Refresh browser. Card type is `custom:evenkeel-boat-card`.

## Manual install

Drop `dist/evenkeel-boat-card.js` into your HA `<config>/www/` directory, then add to **Settings → Dashboards → Resources**:
```
URL:        /local/evenkeel-boat-card.js
Resource:   JavaScript Module
```

## Config schema

```yaml
type: custom:evenkeel-boat-card

# Boat name shown in the header. Optional, default "Boat".
boat_name: Hunter 41DS

# Optional. Captain's Glance entity — its `headline` attribute drives
# the colored sentence at the top of the card.
overall_status: sensor.boat_primary_alert

# Per-zone rollup status entities. State must be one of:
#   "ok" | "warning" | "critical"
# Optional `headline` attribute on each is shown in tooltips.
# Optional `navigate` triggers a Lovelace navigation on tap.
zones:
  bilge:
    rollup:   sensor.boat_bilge_status
    navigate: /lovelace/boat-kelly/bilge
  engine:
    rollup:   sensor.boat_engine_tanks_status
    navigate: /lovelace/boat-kelly/engine
  climate:
    rollup:   sensor.boat_climate_status
    navigate: /lovelace/boat-kelly/climate
  electrical:
    rollup:   sensor.boat_electrical_status
    navigate: /lovelace/boat-kelly/electrical
  weather:
    rollup:   sensor.boat_weather_status
    navigate: /lovelace/boat-kelly/weather
  position:
    rollup:   sensor.boat_position_status
    navigate: /lovelace/boat-kelly/position
  safety:
    rollup:   sensor.boat_safety_status
    navigate: /lovelace/boat-kelly/safety
  system:
    rollup:   sensor.boat_system_status
    navigate: /lovelace/boat-kelly/system

# Animated shore→battery line ("moving ants" pattern).
# Direction reflects sign of battery_a (negative = discharging).
power_flow:
  shore:     binary_sensor.boat_shore_power
  generator: binary_sensor.boat_generator_running
  solar:     sensor.boat_solar_power
  battery_v: sensor.boat_house_battery_v
  battery_a: sensor.boat_house_battery_a

# Up to 6 entities shown in the bottom strip — quick at-a-glance vitals.
footer_vitals:
  - sensor.boat_ais_targets_in_range
  - sensor.boat_apparent_wind_speed
  - binary_sensor.boat_anchor_armed
  - sensor.boat_house_battery_v
```

## Theming

The card uses these CSS variables, falling back to safe defaults:

| Variable | Used for | Fallback |
|---|---|---|
| `--evenkeel-ok` | OK / healthy zone fill | `#22c55e` |
| `--evenkeel-warn` | Warning zone fill, slow pulse | `#f59e0b` |
| `--evenkeel-crit` | Critical zone fill, fast pulse | `#ef4444` |
| `--ha-card-background` | Card background | white |
| `--primary-text-color` | Foreground text | `#1c1c1e` |
| `--secondary-text-color` | Vitals labels | `#5a5a5e` |

Both EvenKeel themes (`evenkeel-minimal`, `evenkeel-marine`) define these tokens. Define them in any other theme to recolor the card without code changes.

## Development

```bash
cd custom-card
npm install
npm run test       # vitest unit + rendering tests
npm run build      # bundles to dist/evenkeel-boat-card.js
npm run watch      # rebuilds on save
```

Vite outputs a single ES-module bundle at `dist/evenkeel-boat-card.js`. CI builds and uploads it as a GitHub Release artifact so HACS users get a clean install.

## Layout

HACS metadata (`hacs.json`, `info.md`) lives at the **repo root**, not
here — that's what the HACS validator expects for `category: plugin`.

```
hacs.json                            # HACS metadata (repo root)
info.md                              # User-facing readme on the HACS install page
custom-card/
  README.md                          # this file
  package.json
  vite.config.ts
  tsconfig.json
  src/
    evenkeel-boat-card.ts            # LitElement entry point
    boat-svg.ts                      # Hunter 41DS SVG markup
    config.ts                        # Config schema + validation
    utils.ts                         # severity / formatting helpers
  test/
    config.test.ts                   # config validation contract
    utils.test.ts                    # pure-function helpers
    rendering.test.ts                # happy-dom Lit smoke tests
  dist/                              # gitignored except .gitkeep
    evenkeel-boat-card.js            # built bundle (CI release artifact)
```

## License

Apache-2.0.
