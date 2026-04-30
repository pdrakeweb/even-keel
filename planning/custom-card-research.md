# EvenKeel Custom Card — Commercial Inspiration Research

**Goal:** Design a Home Assistant Lovelace custom card showing a top-down sailboat diagram with severity overlays (bilge, engine bay, V-berth, tanks, batteries, etc.). Tap a zone → drill into that category.

**Format:** HACS-installable frontend plugin. Single TypeScript/Lit component bundled with Vite.

---

## Sources surveyed

### Commercial chartplotters / instrument suites

| System | Strengths to borrow | Notes |
|---|---|---|
| **B&G H5000 Graphic Display** ([B&G](https://www.bandg.com/bg/type/instruments/h5000graphic-display/)) | 4 Hz update rate. SailSteer (combines wind + heading + targets in one round display). Time-plot widgets (line graphs of wind/heading over time). Sunlight-readable color scheme. | 5" cockpit instrument; not a "boat overview" — it shows nav data, not boat-systems data. Good color/typography reference. |
| **Raymarine Axiom + LightHouse OS** ([Raymarine](https://www.raymarine.com/en-us/our-products/digital-boating/marine-engine-integration)) | Engine dashboard app: rpm, oil P, coolant, fuel rate, range, gear. Up to 5 tanks per dashboard. NMEA 2000-fed. | Engine-centric. Tank rows are bar gauges. No boat-shaped diagram. |
| **Maretron N2KView** ([Maretron](https://www.maretron.com/products/N2KView.php)) | The most flexible commercial "boat overview" tool. Lets you drop digital displays, analog gauges, warning lights, and bar graphs onto an arbitrary background image (you can use a top-down boat photo and pin meters to it). Alerts can email-out on smoke/CO/high bilge. | This is the **architectural twin** of what we're building. Their UX is screenshot-and-imagine, not built-in. |
| **Victron VRM Portal** ([Victron](https://www.victronenergy.com/media/pg/VRM_Portal_manual/en/dashboard.html)) | **Schematic visualization with connecting lines and animated "moving ants"** showing power flow direction. Real-time updates every 2s. Adapts to installed equipment (no inverter? skip the animated lines). | Best inspiration for **animated power flow** between shore/genset/battery/load. Replicable in SVG with `<animateMotion>` or a CSS dasharray animation. |
| **Yacht Devices NMEA gateways with SignalK Kip** ([SignalK Kip](https://github.com/mxtommy/Kip)) | Open-source SignalK web app. Drag-and-drop grid layout. **Zone State Panel widget** monitors many sensors at once with color-coded "zones" + bold status messages from SignalK metadata. AIS radar widget with live targets and range rings. New v3.0 high-impact "snackbar" templates for inform / warn / alert. | Closest open-source analog. Same DNA as us: zones with severity. The Zone State Panel is exactly the rollup pattern we already built. |

### Already-known HA Lovelace techniques

| Project | What we borrow |
|---|---|
| **[ha-floorplan](https://github.com/ExperienceLovelace/ha-floorplan)** | The fundamental approach: an SVG image with `id="some-zone"` elements; map each id to an HA entity; the card swaps fill colors / animates / applies CSS based on entity state. Works as a HACS plugin. |
| **[floorplan-card](https://github.com/chr1st1ank/floorplan-card)** | Per-element click handlers; element-config style. |
| **HA picture-elements card (stock)** | Stack entities as overlays on a background image. Limited but stock. |
| **HA Community 3D floorplans** ([thread](https://community.home-assistant.io/t/3d-floorplan-using-lovelace-picture-elements-card/123357)) | Demonstrates that the pattern works at scale. |

---

## Synthesized design — `<evenkeel-boat-card>`

### Visual

```
┌─────────────────────────── card ────────────────────────────┐
│  Hunter 41DS — All systems good          12:34  •ONLINE     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│        ┌──────────────────────────────────┐                 │
│  ┌────╮│ V-BERTH    GALLEY      ENG-BAY  │                  │
│  │     ││  72°       73°          🔥75°    │ ◀ red overlay   │
│  │  M ││──────╫──────╫────────╫─────│   │   for engine bay │
│  │  A ││ HEAD       NAV          BILGE   │                  │
│  │  S ││ open       72°          ⚠WET    │ ◀ red overlay   │
│  │  T │└─────╫──────╫────────────╫──────┘   for bilge      │
│  │     │                                                    │
│  └────╯                                                     │
│                                                             │
│  Power: ⚡SHORE━━━▶[●BATT 12.6V]━━▶[loads]                   │
│         (animated "moving ants" along the connecting line)  │
│                                                             │
│  📡 8 AIS targets · 🌬 27 kn · ⚓ at slip · ⚡ 12.6 V         │
└─────────────────────────────────────────────────────────────┘
```

### Composition

1. **SVG sailboat (top-down profile)** sized to the card width. Production sailboat profile, plan-view, with named groups:
   - `forepeak`, `v_berth`, `head`, `salon_galley`, `nav_station`, `engine_bay`, `lazarette`, `bilge_overlay`, `cockpit`
2. **Each zone is a `<g>` group** with a fill that the card sets at runtime based on its rollup-status entity:
   - `ok` → translucent green
   - `warning` → translucent amber, 1.5 Hz pulse
   - `critical` → translucent red, 1 Hz pulse, plus a red exclamation badge in the top-right of the zone
3. **Power-flow line** at the bottom: SVG `<path>` with `stroke-dasharray` + animated `stroke-dashoffset` for the Victron-style "moving ants" between shore/gen/solar → battery → loads. Animation direction reflects current direction (charging vs discharging).
4. **Header strip**: boat name + headline from `sensor.boat_primary_alert` + tiny clock + online dot.
5. **Footer strip**: 3-4 always-on icons (AIS count, wind, anchor, batt V) — quickest-glance vital signs. Tom-approved.
6. **Tap any zone** → fires a `tap_action: navigate` to the corresponding drill-down view (`/boat-kelly/bilge`, `/boat-kelly/engine`, etc.).

### Card config schema (Lovelace YAML)

```yaml
type: custom:evenkeel-boat-card
boat_name: Hunter 41DS
overall_status: sensor.boat_primary_alert
zones:
  bilge:
    rollup: sensor.boat_bilge_status
    headline: "{{ state_attr('sensor.boat_bilge_status','headline') }}"
    navigate: /boat-kelly/bilge
  engine:
    rollup: sensor.boat_engine_tanks_status
    headline: "{{ state_attr('sensor.boat_engine_tanks_status','headline') }}"
    navigate: /boat-kelly/engine
  # ... cabin, v_berth, head, galley, lazarette, nav, etc.
power_flow:
  shore: binary_sensor.boat_shore_power
  generator: binary_sensor.boat_generator_running
  solar: sensor.boat_solar_power
  battery_v: sensor.boat_house_battery_v
  battery_a: sensor.boat_house_battery_a
footer_vitals:
  - sensor.boat_ais_targets_in_range
  - sensor.boat_apparent_wind_speed
  - binary_sensor.boat_anchor_armed
  - sensor.boat_house_battery_v
```

### Technical stack

- **Lit** (`lit@3`) — the standard for HA custom cards in 2025/2026. Component-based, reactive, light bundle.
- **TypeScript** — type safety on entity references and config validation.
- **Vite** — bundles to a single `dist/evenkeel-boat-card.js`. Fast HMR for dev (will run inside the running HA's `/local/` directory via volume mount).
- **No external CSS framework** — inline CSS variables that pick up HA theme tokens (`--primary-text-color`, `--ha-card-background`, plus our `--evenkeel-ok`/`-warn`/`-crit`).

### HACS-installable directory layout

Following the [HACS Frontend Plugin spec](https://hacs.xyz/docs/publish/plugin/):

```
custom-card/                  ← HACS-installable repo subdir
  hacs.json                   ← {"name": "EvenKeel Boat Card", ...}
  info.md                     ← User-facing readme shown in HACS UI
  README.md                   ← Developer readme
  package.json
  pnpm-lock.yaml | bun.lockb  (tbd)
  vite.config.ts
  tsconfig.json
  src/
    evenkeel-boat-card.ts     ← LitElement
    boat-svg.ts                ← imported SVG markup as a template literal
    config.ts                  ← TS types for the card config + validation
    utils.ts                   ← color/severity helpers
  test/
    config.test.ts             ← pure-TS unit tests on config validation
    rendering.test.ts          ← Lit testing + JSDOM
  dist/                        ← gitignored except .gitkeep; built by CI
    evenkeel-boat-card.js      ← bundled output (released as GitHub Release asset)
```

### Power-flow animation reference

Victron's "moving ants" pattern in SVG:

```svg
<path d="M shore_x,y L battery_x,y" stroke="var(--evenkeel-ok)"
      stroke-width="2" stroke-dasharray="4 4" stroke-dashoffset="0">
  <animate attributeName="stroke-dashoffset" from="0" to="-8"
           dur="0.5s" repeatCount="indefinite"/>
</path>
```

Direction (charging vs draining) flips by negating `to`. Speed (faster ants under heavy load) modulated by `dur`.

### Severity styling pattern

```css
.zone[data-severity="ok"]       { fill: var(--evenkeel-ok); fill-opacity: 0.3; }
.zone[data-severity="warning"]  { fill: var(--evenkeel-warn); fill-opacity: 0.5;
                                   animation: pulse-warn 1.5s infinite; }
.zone[data-severity="critical"] { fill: var(--evenkeel-crit); fill-opacity: 0.7;
                                   animation: pulse-crit 1.0s infinite; }
@keyframes pulse-crit { 50% { fill-opacity: 1.0; } }
```

The `--evenkeel-ok/-warn/-crit` tokens are already defined in our themes — Modern Minimal uses iOS-style hues, Marine Classic uses brass/walnut/dark-red.

### Sailing (Tom-respectful) details

Adopting from Tom's persona feedback and B&G H5000:
- **Heel indicator**: a thin orange tilt-bar across the bottom of the boat shape (-30° to +30°), only shown if `|heel| > 5°`. Doesn't dominate at-slip.
- **Anchor circle**: when `binary_sensor.boat_anchor_armed == on`, a faint dashed circle around the boat radius at the configured swing radius. Center on actual GPS position relative to anchor point.
- **Lightning warning** (Phase 11 stretch): when Blitzortung integration has any strike <10 nm, overlay a yellow lightning icon on the masthead.

### Sarah-respectful details

Adopting from Sarah's persona feedback:
- **Plain-English aria-labels** on every zone for screen-reader access.
- **Header headline always says who acts** — "Pete is on it" / "Boat is fine. Nothing needs attention right now."
- **No raw entity IDs visible**, ever. Card consumes them; never displays them.

---

## Comparison matrix — what we're matching, what we're NOT matching

| Feature | Commercial best | Our card v1 | Our card v2+ |
|---|---|---|---|
| Top-down boat diagram | Maretron (custom-built per boat) | ✅ Hunter 41DS profile baked-in | Multiple boat-class SVGs selectable |
| Animated power flow | Victron VRM | ✅ moving-ants on shore/gen/solar/battery | Multi-bank, alternator W feed |
| Color-coded zones | Maretron, SignalK Kip | ✅ ok/warn/crit per zone | Configurable thresholds via card config |
| Sunlight readable | B&G H5000 (5" hardware) | n/a (HA tablet) | High-contrast theme variant |
| Tap-to-drill | Maretron, ha-floorplan | ✅ navigate to subview | Long-press for inline detail |
| Wind/heading visual | B&G SailSteer | Footer wind text only | Round wind dial overlay (v2) |
| AIS radar | SignalK Kip, B&G | Footer count only | True radar overlay (v2) |
| Anchor circle | B&G, plotter standard | ✅ when armed | Configurable swing radius |
| Heel meter | B&G | ✅ tilt-bar when underway | Range-marked for boat class |
| Schematic battery wiring | Victron VRM | ✅ shore→batt→load animated | Solar branch, multi-bank |

v1 = Iteration 2 ship target. v2+ = future stretch.

---

## Decisions locked

1. **Tech stack**: Lit + TypeScript + Vite, HACS-installable.
2. **Boat shape**: Hunter 41DS top-down profile, baked into the card. Adding more boat shapes is post-v1.
3. **Animation**: SVG-native (`<animate>` and CSS keyframes). No JS animation lib.
4. **Config**: declarative YAML schema (above). No GUI editor in v1.
5. **Theme integration**: pulls `--evenkeel-ok/-warn/-crit` from active HA theme. Falls back to red/orange/green if unset.
6. **Targets**: any boat owner. Sarah's Modern Minimal theme + Pete's Marine Classic theme both work; the card respects whichever theme is active.

---

## What this enables for the dashboard

Once the custom card lands, the **overview view simplifies dramatically**:

```yaml
# home-assistant/lovelace/kellys-card.yaml — Iteration 2
title: How's My Boat
theme: evenkeel-minimal
views:
  - title: Overview
    path: overview
    cards:
      - type: custom:evenkeel-boat-card
        # … config from the schema above …
      # 3-4 small text widgets for things that don't fit on the diagram
      # (next NOAA forecast, "last seen" timestamps, etc.)
```

The 8 category-button grid we built in iteration 1 stays as a fallback view (`/boat-kelly/legacy`) for users who want it.

---

## Sources

- B&G H5000 Graphic Display product page — https://www.bandg.com/bg/type/instruments/h5000graphic-display/
- B&G H5000 Operation Manual — https://defender.com/assets/pdf/b-g/h5000_om_en_988-10630-003_w.pdf
- SignalK Kip GitHub — https://github.com/mxtommy/Kip
- SignalK Kip 3.0 release — https://signalk.org/2025/kip-300/
- Maretron N2KView product page — https://www.maretron.com/products/N2KView.php
- Maretron Comprehensive Sailboat Example — https://www.maretron.com/examples/sailboats/SailboatComprehensiveSystem.php
- Victron VRM Portal manual — https://www.victronenergy.com/media/pg/VRM_Portal_manual/en/dashboard.html
- Victron new VRM dashboard blog — https://www.victronenergy.com/blog/2020/09/28/new-dashboard-launched-for-vrm/
- Raymarine Marine Engine Integration — https://www.raymarine.com/en-us/our-products/digital-boating/marine-engine-integration
- ha-floorplan — https://github.com/ExperienceLovelace/ha-floorplan
- floorplan-card — https://github.com/chr1st1ank/floorplan-card
- HA community 3D floorplan thread — https://community.home-assistant.io/t/3d-floorplan-using-lovelace-picture-elements-card/123357
- HACS Frontend Plugin spec — https://hacs.xyz/docs/publish/plugin/
