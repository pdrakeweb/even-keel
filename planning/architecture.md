# EvenKeel — Consolidated System Architecture

**Supersedes:** `research/sailboat-monitor-design.md` §§ 5, 6, 8, 11, 12 for the cloud/broker/dashboards layers.
**Companions:** `local-dashboard.md`, `tdd-architecture.md`, `infrastructure.md`, `evaluation-criteria-and-dashboard-simulation.md`, `hardware-deep-dive.md`.

---

## 1. One-Diagram View

```
╔════════════════════════════════════════ HUNTER 41DS ═══════════════════════════════════════╗
║                                                                                            ║
║  ┌─────────────────────────┐   3-wire UART     ┌────────────────────────────────────┐      ║
║  │ Wegmatt dAISy HAT       │ ─────────────────►│ BoatMon-1: ESP32-S3-DevKitC-1      │      ║
║  │ (AIS RX on 87B/88B)     │                   │   firmware = ESPHome               │      ║
║  └─────────────────────────┘                   │                                    │      ║
║                                                │   ┌───────────────────────────┐    │      ║
║  ┌─ Sensors (I2C, 1-wire, GPIO) ──────────────►│   │ stream_server TCP :6638   │    │      ║
║  │  DS18B20 × 3 (cabin/eng/fridge, → 10)       │   │ MQTT/TLS client → local   │    │      ║
║  │  INA226 (house V/A)    ADS1115 (tanks)      │   │ web_server v3 (Tier 2)    │    │      ║
║  │  V-divider (start batt)                     │   │ native API (LVGL sibling) │    │      ║
║  │  opto-iso × 2 (shore + gen)                 │   │ GPIO → LED + piezo (T0)   │    │      ║
║  │  float switch (bilge)   BME280 (cabin)      │   └───────────────────────────┘    │      ║
║  │  GPS u-blox NEO-M9N on UART2 (Phase 8)      │                                    │      ║
║  │  Victron BLE advertisements (Phase 7)       │                                    │      ║
║  └──────────────────────────────────────────── └──────┬─────────────────────────────┘      ║
║                                                       │ WiFi, boat LAN                    ║
║  ┌────── Tier 0: LED + piezo buzzer ────────┐         │                                   ║
║  │ Wired off BoatMon-1 GPIO (not via LVGL)  │         │                                   ║
║  │ Always on; $3; watches bilge/battV/online│         │                                   ║
║  └──────────────────────────────────────────┘         │                                   ║
║                                                       │                                   ║
║  ┌────── Tier 1: ESP32-S3 + Waveshare 4.3" LCD (LVGL via ESPHome) ────────┐   (Phase 10)  ║
║  │ Nav-station panel; subscribes to same MQTT (+ native API fallback)    │                ║
║  │ Red/night mode; Tier 0 remains independent                            │                ║
║  └────────────────────────────────────────────────────────────────────── ┘                ║
║                                                       │                                   ║
║  ┌──────────────────────────────────────────────────  ▼  ────────────────────────────┐    ║
║  │ Raspberry Pi 4 4GB + USB SSD (HA OS)                                              │    ║
║  │   • Mosquitto add-on = PRIMARY boat broker (MQTT/TLS :8883)                       │    ║
║  │   • optional: on-boat HA instance (headless broker + local fallback dashboard)    │    ║
║  └──────────────────────────────────────────────┬───────────────────────────────────┘     ║
║                                                 │                                         ║
║  ┌─ Onboard 4×4 MIMO X75 LTE router (WG CLIENT) ┴────────────────────────────────┐        ║
║  │  Boat LAN 10.20.0.0/24                                                        │        ║
║  │  WireGuard tunnel OUTBOUND to home router (CGNAT-safe)                        │        ║
║  │  Fallback AP BoatMon-Fallback (for on-boat recovery when LTE is dead)         │        ║
║  └───────────────────────────────────┬───────────────────────────────────────────┘        ║
╚══════════════════════════════════════╪════════════════════════════════════════════════════╝
                                       │ WireGuard over LTE (or marina WiFi if joined)
                                       ▼
╔══════════════════════════════════════╪══════════════ HOME ═══════════════════════════════╗
║                                      │                                                   ║
║  ┌─ Home router (WG SERVER) ─────────┴────────┐                                           ║
║  │  Home LAN                                  │                                           ║
║  │  Pete's phone (WG CLIENT) over mobile data │                                           ║
║  └────────────┬───────────────────────────────┘                                           ║
║               │                                                                           ║
║  ┌────────────▼─────────────────────────────────────────────────────────────────┐         ║
║  │ Home Assistant Green ($99, one-time)                                         │         ║
║  │   • Mosquitto add-on  ─── BRIDGE ───► boat Mosquitto                         │         ║
║  │   • HA core (automations, recorder, dashboards)                              │         ║
║  │   • ESPHome dashboard (OTA from home via WG)                                 │         ║
║  │   • OPTIONAL: aisstream.io forwarder add-on (pulls boat TCP :6638 via WG,    │         ║
║  │               forwards to aisstream.io — off by default)                     │         ║
║  │   • OPTIONAL: Cloudflare Tunnel for https://ha.peteskrake.com remote URL     │         ║
║  └─────────────────────────────┬────────────────────────────────────────────────┘         ║
║                                │                                                          ║
║  ┌─ Kelly's 10" wall tablet ───▼──┐      ┌─ Pete's phone (home OR via WG away) ──┐        ║
║  │ Fully Kiosk Browser PWA        │      │ HA companion app                      │        ║
║  │ "How's My Boat" card           │      │ Full dashboard                        │        ║
║  └────────────────────────────────┘      └───────────────────────────────────────┘        ║
╚═══════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Architectural Layers

### 2.1 Firmware (BoatMon-1 ESP32-S3)
- **ESPHome YAML**, organized into packages (`base`, `network`, `ais`, `temperature`, `power`, `bilge`, `health`, `victron`, `gps`, `tanks`, `test_mode`).
- External components: `github://tube0013/esphome-stream-server-v2`, `github://Fabian-Schmidt/esphome-victron_ble`.
- **Test-mode injection**: when compiled with `-D ENABLE_TEST_MODE`, each real sensor is wrapped in a `template` sensor that returns MQTT-injected values. HMAC-gated, auto-expires. See [`tdd-architecture.md §C`](tdd-architecture.md).
- Emits MQTT/TLS to **boat Mosquitto** (not cloud). Exposes AIS on TCP :6638 for local OpenCPN etc. Exposes Tier 2 dashboard on HTTP :80 via `web_server v3 (local: true)`.
- Hardware-brick safety: Tier 0 LED/buzzer driven directly off GPIO, not through any intermediate service.

### 2.2 Firmware (DashboardHead-1 ESP32-S3, Phase 10)
- Separate ESPHome YAML, separate device. Waveshare ESP32-S3-Touch-LCD-4.3 hardware.
- Subscribes to BoatMon-1 via **native API** (primary) with **MQTT fallback**.
- LVGL pages: Home, Power, Temps, AIS-list (Phase 10+), Settings.
- Night mode: GPIO toggle → LVGL red/black theme + 5% backlight PWM.
- No independent sensor reads; pure display device.

### 2.3 On-boat Pi (broker, optional local HA)
- Raspberry Pi 4 4GB + 128 GB USB SSD running HA OS.
- **Mosquitto add-on** is the PRIMARY MQTT broker. TLS via Let's Encrypt DNS-01 certs renewed from home, shipped to boat.
- On-boat HA instance is OPTIONAL — runs a minimal Lovelace for dockside admin without WG.
- Power: ~3.5 W typical = ~0.3 Ah/hr at 12 V (fed from the ESP32's UPS branch or a dedicated 5 V rail).

### 2.4 Home host (HA Green)
- Stock HAOS. Mosquitto add-on = **bridge client** to boat broker (topic `boat/# both 1`).
- Recorder retains ~10 days SQLite; InfluxDB add-on optional for longer retention.
- ESPHome dashboard installed; OTA to BoatMon-1 and DashboardHead-1 goes via WG.
- Optional AIS forwarder add-on (see §2.6).
- Optional Cloudflare Tunnel sidecar for `https://ha.peteskrake.com`.

### 2.5 Networking
- **WireGuard**: home router is SERVER. Boat router + Pete's phone are CLIENTS. UDP :51820 forwarded on home router.
- Boat LAN `10.20.0.0/24`. Home LAN per existing. WG tunnel `10.99.0.0/24`.
- MQTT bridge is the only traffic on the tunnel in normal operation (~5 MB/day).
- DNS inside the tunnel via the home router (entries: `boat-broker.int`, `boatmon-1.int`, `dashboard-head.int`).

### 2.5.1 Power subsystem (decision locked — USB-C in, user's choice upstream)

Per the [simplicity review](simplicity-review.md) §3.2, all 12 V handling is moved **outside** the boat-node enclosure. The enclosure has one interface: a panel-mount USB-C receptacle. How 5 V gets there is the user's choice:

| Option | Part | Use case |
|---|---|---|
| **Marine USB-C outlet** | Scanstrut ROKK Charge+ USB-C (~$65) | Permanent install, 12V hard-wired to house bank, ISO 7637-2 surge protection built in |
| **Automotive USB-C adapter** | Anker PowerDrive III Duo (~$20) + pigtail | Cheaper install; plug into a 12V accessory socket |
| **Pass-through UPS** | Anker 733 GaNPrime PowerCore (~$110) | Optional battery backup; ~20 h runtime if 12V lost |
| **Wall brick** | Any USB-C PD 20W+ | Bench testing / marina-shore-power-only setups |

Inside the enclosure: no fuse, no TVS, no buck, no bulk cap. Certified external products handle it. Feather ESP32-S3 idles ~100 mA; peaks ~400 mA with all sensors + dAISy. 10 W PD is more than enough.

NF-3 ("12 h UPS runtime") remains a **user-configurable optional feature** — pick option 3 above to satisfy it.

### 2.5.2 Home-independence constraint (decision locked)

**The boat application must not require the home network to be reachable.** Home HA is the default path for dashboards and alert fan-out, but is not a single point of failure for critical alarms. Three independent layers deliver critical alerts:

1. **Tier 0 — on-boat LED + piezo buzzer** (GPIO-direct off BoatMon-1). Always works while ESP32 + 12 V are alive.
2. **Direct-from-boat Pushover notification.** ESPHome `http_request` POST straight to `api.pushover.net` over LTE. One-time app fee, no subscription. Fires independently of home HA or broker bridge.
3. **HA-mediated alerts** (HA Companion push, TTS, email, optional Twilio SMS for users with their own Twilio subscription). Delivered when home HA is reachable from the boat broker via the WireGuard bridge.

Routing policy: **critical alerts** (bilge wet, anchor drag, boat offline) fire on Layer 1 + Layer 2 unconditionally, and Layer 3 when available. **Non-critical alerts** (low battery, shore power lost at slip, generator started) fire on Layer 3 only — avoids waking Pete's phone during normal LTE/home hiccups.

### 2.6 AIS pipeline
- **Local path:** dAISy → ESP32 UART → `stream_server` :6638 → any LAN consumer (OpenCPN, chartplotter).
- **Home path:** home HA pulls :6638 over WG for local consumption and optional forwarding.
- **Optional contribution:** home HA add-on (Python) forwards per-line AIVDM to aisstream.io. **Off by default.** Single config toggle. Failure of aisstream doesn't affect the boat.

### 2.6.5 Sensor expansion architecture

EvenKeel uses a **six-tier expansion model** so the v1 boat node can grow from 5 to 30+ sensors without re-architecture. Detail in [`sensor-expansion.md`](sensor-expansion.md) and [`nmea2000-integration.md`](nmea2000-integration.md).

| Tier | Mechanism | Sensors | Cost |
|---|---|---|---|
| 1 | Direct Qwiic chain | 3–5 within ≤1m | $5–15 each |
| 2 | TCA9548A I²C mux (1→8 channels, cascadable to 64) | up to 64 | $7 mux + sensors |
| 3 | 1-Wire daisy chain (DS18B20 only) | up to 30, ≤50m | $8 per probe |
| 4 | Satellite ESP32 nodes (QT Py / XIAO over WiFi MQTT) | unlimited | $15–25 + local sensors |
| 5 | Wireless ecosystems — BLE, Zigbee (Sonoff ZBDongle-E on Pi), LoRa | unlimited | $5–50 each |
| **6** | **Existing-bus integration — N2K, NMEA 0183, J1939, VE.Direct, Modbus, dry-contact** | unlimited (read-only) | $60 (DIY) – $185 (SignalK gateway) |

Same firmware repo, same broker, same HA dashboards across all tiers. Tier 5 leverages HA's native integrations at zero firmware cost. Tier 6 leverages the boat's *existing* sensors and instruments — read-only — and can replace Phase 8's GPS hardware entirely if the chartplotter already has a GPS on the N2K backbone.

### 2.7 Dashboards (surfaces and themes)

**Surfaces:**
- **On-boat Tier 0 LED+buzzer** (Phase 3) — unconditional safety alarm.
- **On-boat Tier 2 ESPHome web_server** (Phase 4) — phones on boat LAN.
- **Kelly's "How's My Boat" card** (HA Lovelace, home tablet, Phase 5) — minimal at-a-glance.
- **Pete's "Power User" dashboard** (HA Lovelace, Phase 10) — dense diagnostic view.
- **On-boat Tier 1 LVGL panel** (Phase 11+) — always-on nav-station display.

**Themes (locked):**
- **Modern Minimal** (default) — iOS-style, generous whitespace, calm-until-it-matters. Applies to Kelly's card and Tier 2 PWA.
- **Marine Classic** (alternate) — brass gauges, navy + wood, B&G/Raymarine-style. One-click toggle in HA profile / ESPHome settings.
- **Data-Dense Grafana** (Pete only) — dense monospace cockpit. Separate Lovelace view `/lovelace/pete-power`; not surfaced on Kelly-facing dashboards.

See [`mockups/README.md`](mockups/README.md) for visual references and [`mockups/01-marine-classic.html`](mockups/01-marine-classic.html), [`02-modern-minimal.html`](mockups/02-modern-minimal.html), [`03-data-dense.html`](mockups/03-data-dense.html).

### 2.8 Test harness
- `pytest-bdd` as the only runner.
- Gherkin `.feature` files organized by user-visible capability (alerts, telemetry, AIS, dashboard, resilience), tagged by phase.
- Single `BoatAdapter` protocol, three implementations: `VirtualAdapter` (Wokwi + Docker MQTT/HA), `HilAdapter` (serial to bench stimulator), `LiveIntegrationAdapter` (MQTT test-mode topics to deployed firmware).
- Visual regression via Playwright `toHaveScreenshot()` with locator-scoped snapshots.
- LVGL panel testing via LVGL's SDL PC simulator, shimmed to consume test-harness MQTT.
- CI: GitHub Actions, virtual mode every push; self-hosted runner in Pete's garage for HIL mode on tagged releases.

### 2.9 Evaluation criteria
- ~60 measurable criteria across Safety, Reliability, At-a-glance Usability, Alert Delivery, Observability, Maintainability, Cost ($0/mo ongoing), Power, Network, Security, Extensibility, Data Portability, Testability.
- Every criterion maps to either an automated test, a manual check, or a hybrid — see [`evaluation-criteria-and-dashboard-simulation.md`](evaluation-criteria-and-dashboard-simulation.md).
- Phase exit gates = all Must-have criteria for that phase, green.

---

## 3. Data Flow Summary

| Flow | Path |
|---|---|
| Sensor telemetry | ESP32 → boat Mosquitto → (WG) → home Mosquitto bridge → home HA → Kelly's card / Pete's dashboard |
| Bilge alarm (3 independent layers) | ESP32 GPIO → Tier 0 LED+buzzer (on boat) **AND** ESP32 → Pushover API direct over LTE (to Pete's phone, no HA required) **AND** MQTT → home HA → push/TTS/email to Pete + Kelly (when HA is reachable) |
| AIS to boat | dAISy → ESP32 UART → stream_server :6638 → LAN consumers |
| AIS to home | stream_server :6638 → (WG) → home HA (for local viewing) |
| AIS to aisstream (optional) | home HA add-on → aisstream.io |
| Kelly's tablet | home LAN → home HA Lovelace PWA |
| Pete remote | Pete's phone → (WG) → home HA → live data (or Cloudflare Tunnel convenience URL) |
| OTA | Pete's laptop → (WG) → home HA ESPHome dashboard → (WG) → boat LAN → ESP32 |
| Test-mode stimuli | Test runner → (virtual: Wokwi; HIL: bench ESP32; live: MQTT to `boat/hunter41/test/*`) |

---

## 4. Failure Modes (summary — full table in [`infrastructure.md §9`](infrastructure.md))

The critical invariant EvenKeel is built around: **the bilge alarm always reaches Kelly's tablet within 30 seconds** as long as (home ISP + home HA + boat LTE + boat Pi + ESP32) are all up. If ANY of the middle links fail:

- **LTE dies**: Kelly sees "OFFLINE" banner. Tier 0 LED+buzzer still fires on the boat itself.
- **Home internet dies**: Tier 0 fires on the boat; home HA shows stale values; recovery on reconnect.
- **Boat Pi dies**: Tier 0 fires (direct GPIO); MQTT telemetry stops; HA marks offline. **Degraded but safe.**
- **ESP32 dies**: nothing works. Tier 0 silent. Only defense is the watchdog-ESP32 v2 feature or hardware-independent traditional bilge alarm (boat's own existing alarm system — not replaced by EvenKeel).

---

## 5. Security Posture

- MQTT auth + ACLs per device. Pete-user can read anything; firmware accounts write only to their subtree.
- TLS on all broker connections, including inside the WG tunnel (defense in depth; also keeps the home↔boat broker bridge TLS-consistent).
- OTA restricted to local LAN and WG-tunneled access only. Password-protected & encrypted (`ota:` with key).
- `test_mode` shipped in production firmware; HMAC-gated `enable` topic; auto-expiring; audit-logged to HA.
- No passwords/keys in Git. **Public repo** — this is non-negotiable enforcement. `secrets.yaml.example` in repo; real `secrets.yaml` gitignored. Pre-commit hook scans for obvious key patterns; GitHub Actions secret-scanning enabled.
- Domain-email Let's Encrypt contact. Rotate MQTT passwords at domain renewal time.
- **Home router WireGuard port (UDP :51820) exposed publicly.** WireGuard's design means unauthenticated packets get no response — the port is effectively invisible to scanners. Harden further with: (a) no other inbound ports; (b) router firewall drops all non-WG traffic at UDP :51820; (c) WG peer keys regenerated annually; (d) fail2ban-style UDP rate limiting if the router supports it. Additional attack surface from this exposure is near-zero.
- Pushover API token lives only in the boat ESP32's `secrets.yaml`; scoped to the boat device only. Rotation: annual.

---

## 6. What's Explicitly NOT in Scope

From the prior design plus the EvenKeel additions. Note the refined N2K stance — *read-only* listening is now permitted (Tier 6), but writing or replacing the chartplotter is not.

**Forbidden:**
- ❌ Chartplotter / navigation display replacement
- ❌ Writing to NMEA 2000 / 0183 buses (read-only listener only)
- ❌ Acting as primary nav data source — chartplotter remains source of truth
- ❌ Real-time collision avoidance (dAISy not rated)
- ❌ Remote engine start (out of scope indefinitely)
- ❌ Calibrating boat instruments via EvenKeel (their own UIs only)
- ❌ Any feature that requires a recurring payment to a third party

**Permitted (Phase 11+):**
- ✅ Reading N2K, 0183, J1939, VE.Direct, Modbus traffic for telemetry purposes
- ✅ Republishing decoded values to HA via the existing MQTT bridge
- ✅ Engine RPM via alternator-W tap or via N2K (if newer engine)
- ✅ Wind / depth / speed via N2K read (if instruments installed)

**Deferred but still permitted scope:**
- BME280 cabin pressure is weather-flag only, not nav-rated — already in plan
- Barometric trend storm warning — already in plan

---

## 7. Traceability

This consolidated architecture traces back to specific research outputs:

| Concern | Source |
|---|---|
| Firmware layout, ESPHome components | `research/sailboat-monitor-design.md` §§ 11, 17 |
| Broker topology, WG topology, failure modes | [`infrastructure.md`](infrastructure.md) §§ 2, 3, 9 |
| Tier 0/1/2 dashboards, LVGL panel spec | [`local-dashboard.md`](local-dashboard.md) §§ Tiered Architecture, Content Spec |
| BDD framework, adapter interface, test mode | [`tdd-architecture.md`](tdd-architecture.md) §§ A, C |
| BOM, power subsystem, actuator safety | [`hardware-deep-dive.md`](hardware-deep-dive.md) |
| Evaluation criteria, acceptance gates | [`evaluation-criteria-and-dashboard-simulation.md`](evaluation-criteria-and-dashboard-simulation.md) § A, E |
