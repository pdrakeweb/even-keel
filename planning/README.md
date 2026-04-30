# EvenKeel — Planning Folder

**Project:** EvenKeel — a DIY sailboat monitoring, AIS, telemetry, and alerting system for the Hunter 41DS at Safe Harbor Sandusky.
**Stage:** Planning complete; Phase 1 implementation not yet started.
**Repo root:** `C:\Users\pdrak\Documents\Source\even-keel`
**Prior art:** `research/sailboat-monitor-design.md` (v1.0) + `research/sailboat-monitor-continuation-brief.md`.

---

## What EvenKeel Is (one paragraph)

EvenKeel is a single-ESP32-S3 boat node plus supporting infrastructure — on-boat Raspberry Pi, at-home Home Assistant, optional touchscreen dashboard — that gives Pete and Kelly at-a-glance knowledge of *where the boat is, what it's doing, and how it is*. It receives AIS, reads house telemetry (batteries, temps, bilge, shore/gen/battery, tanks, GPS), provides dashboards both **on the boat** and **at home**, fires alarms for safety-critical events, runs on low-power DIY hardware only, and requires **zero** cloud subscriptions or mandatory third-party services. Every feature is designed to be verifiable by natural-language test scenarios that run against both a simulated boat and the real deployed system.

---

## How This Folder Is Organized

| File | What's in it | Read when |
|---|---|---|
| [`README.md`](README.md) | This file — map of the planning folder | Start here |
| [`architecture.md`](architecture.md) | Consolidated system architecture across firmware, infra, dashboards, and testing | Understand how the pieces fit |
| [`roadmap.md`](roadmap.md) | Phased implementation plan, rewritten for EvenKeel's cloud-free direction | Deciding what to build next |
| [`open-questions.md`](open-questions.md) | Consolidated & deduped open questions + Pete's resolutions | Deciding what to answer next |
| [`simplicity-review.md`](simplicity-review.md) | **DIY simplicity pass** — plug-together parts, USB-C-only power, Shelly for AC, pre-wired probes | Before ordering parts |
| [`diagrams/hardware.md`](diagrams/hardware.md) | Mermaid hardware block diagrams, pinout, power tree, enclosure, HIL rig | Wiring and ordering parts |
| [`diagrams/hardware-visuals.html`](diagrams/hardware-visuals.html) | **SVG illustrations** — boat elevation, enclosure interior, front panel, pinout card, power chain, wiring, topology | Seeing what the hardware looks like |
| [`diagrams/software-flows.md`](diagrams/software-flows.md) | Mermaid data flows, state machines, alert routing, test harness | Understanding runtime behavior |
| [`mockups/`](mockups/) | **5 HTML dashboard design mockups** — double-click to preview | Choosing visual direction |
| [`sensor-expansion.md`](sensor-expansion.md) | **6-tier sensor expansion architecture** — how to scale from 5 to 30+ sensors | Adding new sensors after v1 |
| [`nmea2000-integration.md`](nmea2000-integration.md) | **Tier 6 detail** — NMEA 2000, 0183, J1939, VE.Direct, Modbus integration | Tapping into existing boat instruments |
| [`local-dashboard.md`](local-dashboard.md) | Research: on-boat local dashboard options (Tier 0/1/2 design) | Designing the nav-station display |
| [`tdd-architecture.md`](tdd-architecture.md) | Research: natural-language BDD tests, virtual/HIL/live adapters, simulation stack | Setting up the test harness |
| [`infrastructure.md`](infrastructure.md) | Research: zero-subscription infra; broker-on-boat + HA-at-home; failure modes | Setting up networking, brokers, hosts |
| [`evaluation-criteria-and-dashboard-simulation.md`](evaluation-criteria-and-dashboard-simulation.md) | Research: measurable criteria rubric + dashboard simulation stack | Deciding what "done" means |
| [`hardware-deep-dive.md`](hardware-deep-dive.md) | Research: validated BOM; MCU/AIS/sensor/actuator deep dive; availability | Ordering parts |

---

## Key Design Shifts vs. Prior Research

The prior design doc (`research/sailboat-monitor-design.md` v1.0) is the starting point. EvenKeel differs on four pivots:

1. **No cloud dependency.** The OCI Always-Free MQTT + AIS relay is replaced by an on-boat Mosquitto + home HA bridge over WireGuard. aisstream.io contribution becomes an opt-in add-on. Nabu Casa and metered backup services are forbidden. See [`infrastructure.md`](infrastructure.md).
2. **On-boat dashboard is first-class.** The prior design only surfaced dashboards at home. EvenKeel adds a tiered on-boat display: a $3 LED+buzzer for critical alarm, a ~$50 ESP32-S3 + 4.3" LVGL panel at the nav station, and the existing ESPHome `web_server` on phones. See [`local-dashboard.md`](local-dashboard.md).
3. **Test-driven architecture.** Natural-language Gherkin scenarios run in three modes — virtual (Wokwi + Docker HA), HIL (bench rig + real firmware), and live (MQTT test-mode against deployed hardware) — via a common adapter interface. See [`tdd-architecture.md`](tdd-architecture.md).
4. **Explicit evaluation criteria.** ~60 measurable criteria across 13 categories (Safety, Reliability, At-a-glance Usability, etc.) gate each phase. See [`evaluation-criteria-and-dashboard-simulation.md`](evaluation-criteria-and-dashboard-simulation.md).

---

## Major Decisions Locked

| Area | Decision |
|---|---|
| Boat MCU | ESP32-S3-DevKitC-1-N16R8V (final) |
| Firmware framework | ESPHome (YAML) with `stream_server`, `victron_ble`, `lvgl` external components |
| AIS receiver | Wegmatt dAISy HAT via breakout pads |
| Enclosure | Polycase WC-23F (or Bud NBB-15242) |
| Boat power | 12V → fuse → TVS → USB-C PD buck → pass-through bank OR 10Ah LiFePO4 drop-in UPS |
| Broker location | **On the boat** (Mosquitto on a Raspberry Pi 4 4GB + SSD running HA OS) |
| Home host | **Home Assistant Green** ($99, one-time) |
| Network | Home router as WireGuard SERVER; boat router + Pete's phone as clients |
| AIS forwarding | Optional aisstream.io contribution via HA add-on, off by default |
| Local dashboard | Tier 0 LED+buzzer; Tier 1 ESP32-S3 + Waveshare 4.3" LVGL panel (Phase 10); Tier 2 ESPHome `web_server` on phones (Phase 4) |
| BDD framework | **pytest-bdd** |
| Simulator | **Wokwi** (free for public repos) + Docker Mosquitto + Docker HA |
| CI | GitHub Actions running virtual tests; self-hosted runner for HIL |
| Backup | Git-versioned config + local NAS rsync + monthly USB copy |

---

## Major Decisions Still Open

See [`open-questions.md`](open-questions.md) for the consolidated list. The most consequential are:

- **UPS path**: USB-C pass-through bank (Path A, cheaper) vs. 10Ah LiFePO4 drop-in (Path B, more runtime & marine-native)
- **On-boat LVGL panel in v1** vs. defer to Phase 10 (after one sailing season of data on what crew actually checks)
- **CGNAT status** of Pete's home ISP and the LTE carrier (determines WireGuard topology)
- **Actuator scope** in v1 vs. v1.5 (with safety interlocks)
- **Boat asleep off-season** — low-power always-on broker or accept "offline" for months

---

## Repo Directory Plan

The planning folder above is just planning. The actual implementation lives in sibling directories:

```
even-keel/
  research/           # original design docs (Pete + prior Claude)
  planning/           # THIS FOLDER — research reports + synthesis
  firmware/           # ESPHome YAML, external components pinning, secrets template
    boat-mon.yaml
    dashboard-head.yaml    # Phase 10 LVGL panel
    packages/
    secrets.yaml.example
  tests/              # Gherkin features + pytest-bdd + adapters
    features/
    steps/
    adapters/
    wokwi/
    docker/
    samples/
    snapshots/
  hil-rig/            # bench HIL rig firmware + BOM
  home-assistant/     # HA OS configuration (Git-versioned)
    configuration.yaml
    lovelace/
      kellys-card.yaml
      petes-dashboard.yaml
    automations/
    blueprints/
  relay/              # optional aisstream.io forwarder (HA add-on or systemd svc)
  docs/               # user-facing docs; runbooks; photos
  tools/              # one-off scripts (MQTT replay, AIS capture, cert rotation)
  .github/workflows/  # CI
  .gitignore
  README.md
  LICENSE
```

The `research/` and `planning/` folders are documentation. Everything in `firmware/`, `tests/`, `home-assistant/`, etc. is implementation.

---

## Next Steps (once open questions are resolved)

1. Resolve the top 5-10 open questions with Pete.
2. Scaffold the repo directories per above.
3. Begin Phase 1 (bench prototype: AIS → local TCP on bench ESP32) with pytest-bdd harness set up in parallel.
4. Establish the CI pipeline early — even a single passing Wokwi-based scenario is worth the setup friction.
