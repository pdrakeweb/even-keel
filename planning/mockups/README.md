# EvenKeel — Dashboard Design Mockups

Five intentionally disparate visual directions for the EvenKeel local UI (on-boat phone PWA / eventual Tier 1 panel) and the Home Assistant dashboard cards. Each mockup is a single self-contained HTML file — double-click to preview in any browser. No dependencies beyond Tailwind via CDN.

Each mockup shows the **same three states** side-by-side so you can compare how each direction handles severity and information density:

1. **All OK** — at the slip, shore power, batteries nominal
2. **Warning** — underway, low house battery, generator running
3. **Critical** — bilge water detected (the alarm state)

And shows **two surfaces per direction:**

- 📱 **Boat-side phone PWA** (crew on boat LAN opening `http://boatmon-1.local/`)
- 📊 **Home HA Lovelace card** (Kelly's kitchen tablet)

## The Five Directions

| # | Name | Voice | Best for |
|---|---|---|---|
| [01 Marine Classic](01-marine-classic.html) | Traditional gauges, brass & navy, B&G/Raymarine aesthetic | Formal, nautical, serious | Pete — looks at home on a real boat |
| [02 Modern Minimal](02-modern-minimal.html) | iOS/Apple Weather style, big numbers, generous whitespace | Calm, uncluttered, premium | Kelly — easy to read at a glance |
| [03 Data-dense Grafana](03-data-dense.html) | Dark DevOps cockpit, charts + sparklines, small text | Technical, expert, powerful | Pete — diagnosing / monitoring |
| [04 Glance High-Contrast](04-glance-high-contrast.html) | Enormous type, traffic-light colors, almost no chrome | Unambiguous, readable at 10 ft | Helm / Kelly's 3-second check |
| [05 Playful Friendly](05-playful-friendly.html) | Rounded, warm, illustrated, encouraging copy | Welcoming, approachable, low-jargon | Kelly — non-technical, inviting |

## Shared design system (what all five agree on)

Regardless of direction, every mockup follows these rules:

- **Severity color hierarchy:** green = OK, amber = warning, red = critical. Red is never used for non-alarms.
- **Bilge gets the biggest glyph.** In every design, the bilge state is visually dominant when wet.
- **"Boat online" is always visible.** Either as a header pill, a banner, or a color on the boat icon itself.
- **No horizontal scroll on mobile.** All phone layouts fit 375px wide.
- **Uses only Material Design Icons** (via MDI web font or inline SVG) — matches Home Assistant's icon set for Lovelace consistency.
- **Works in light mode.** Night mode is a deliberate per-direction addition, not assumed.

## What each mockup does NOT lock down

These are **visual direction** mockups, not final specs. Each still needs:

- Responsive breakpoints for tablet vs phone
- Accessibility audit (color contrast for red/green-deficient users)
- Red-at-night variants for any surface mounted on the boat
- Real data-bound versions (current mockups are static HTML)
- Animation/transition spec when state changes

## Decision locked (Pete, April 2026)

- **#1 Marine Classic** and **#2 Modern Minimal** — BOTH ship as selectable themes. User chooses in HA/ESPHome settings. Default = Modern Minimal (easier read for the family); Marine Classic is a one-click theme switch.
- **#3 Data-Dense Grafana** — ships as an **optional "Power User" dashboard** — a separate Lovelace view (`/lovelace/pete-power`) that's not on the main Kelly-facing dashboard. Targeted at Pete for diagnostics.
- **#4 Glance High-Contrast** — revisit if/when the Tier 1 on-boat LVGL panel is built (Phase 11+). Not included in v1 themes.
- **#5 Playful Friendly** — not taken forward. Useful voice notes for copy (plain-English alert descriptions) carry into the other themes' microcopy.

### Theme implementation plan

| Surface | Default | Alternate |
|---|---|---|
| Kelly's HA "How's My Boat" card | **Modern Minimal** | Marine Classic (user toggle) |
| Phone PWA on boat (Tier 2) | **Modern Minimal** | Marine Classic (user toggle) |
| Pete's Power User dashboard | **Data-Dense Grafana** | — |
| Any eventual Tier 1 LVGL panel (Phase 11+) | TBD at that time | Likely Marine Classic + Glance hybrid |

Technical realization:
- HA Lovelace themes defined in `home-assistant/themes/evenkeel-minimal.yaml` and `evenkeel-marine.yaml`. User switches via HA profile settings.
- ESPHome `web_server v3` supports a single baked-in stylesheet; we'll ship two firmware targets or a runtime CSS swap driven by a settings endpoint.
- Icon set: Material Design Icons throughout (both themes). Color tokens differ per theme; typography and icon choices shared.
