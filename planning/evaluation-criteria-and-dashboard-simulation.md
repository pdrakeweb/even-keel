# EvenKeel — Evaluation Criteria & Dashboard Simulation Plan

**Project:** EvenKeel sailboat monitoring (Hunter 41DS, Safe Harbor Sandusky)
**Companion docs:** `research/sailboat-monitor-design.md` (v1.0), `research/sailboat-monitor-continuation-brief.md`
**Document version:** 1.0 — April 2026
**Purpose:** Define testable success criteria for the system and concrete ways to iterate on dashboards before any hardware exists.

---

## A. Evaluation Criteria Framework

### A.1 Rubric format

Every criterion has: **ID**, **Category**, **Name**, **Target/Threshold**, **Measurement Method**, **Priority** (M = Must, S = Should, N = Nice), and **Test Mode** (A = Automated, M = Manual, H = Hybrid). Priorities map to v1 exit gates: all M-priority criteria must pass before Phase 6 sign-off; S-priority are acceptable known gaps tracked in the risk register; N-priority are backlog.

### A.2 Criteria table

| ID | Category | Name | Target | Measurement | Priority | Test |
|---|---|---|---|---|---|---|
| **SAFE-1** | Safety | Bilge float alarm → push notification | ≤ 30 s p95, ≤ 60 s p99 from GPIO transition to phone receipt | Inject GPIO low→high on ESP32 via `button` test platform; timestamp on MQTT publish vs. phone push log | M | H |
| SAFE-2 | Safety | Bilge alarm persists through MQTT outage | Alarm redelivered within 60 s of broker reconnect, no loss | Kill broker for 5 min while tripping float; verify HA receives event on reconnect (retained+LWT) | M | A |
| SAFE-3 | Safety | Offline watchdog notification | Push to Pete within 15 min of ESP32 going silent (heartbeat gap >5 min, confirm alert at 15 min) | Power-cycle ESP32; measure elapsed time to "boat offline" push | M | A |
| SAFE-4 | Safety | Low-house-battery alarm | Notify when house V < 11.8 sustained 5 min, no flapping | Simulate via `template_sensor` override; confirm single alert, no repeat within 1 h | M | A |
| SAFE-5 | Safety | Shore-power-lost during storm | Push to Pete within 2 min of opto-isolator drop when home weather entity reports lightning within 25 mi | Inject shore=0 + mock weather entity in HA | S | A |
| SAFE-6 | Safety | Anchor drag detection (Phase 9) | Alert within 60 s of position deviation >50 m from armed anchor point | Mock GPS publish to MQTT in drift pattern | S | A |
| SAFE-7 | Safety | Slip geofence breach | Alert within 60 s of leaving polygon | Mock GPS publish outside polygon | S | A |
| SAFE-8 | Safety | Fire / high-temp alarm (engine compartment) | Alert at >70 °C sustained 60 s | DS18B20 immersed in warm water bench rig OR virtual override | M | H |
| SAFE-9 | Safety | Intrusion (future hook) | N/A v1 — placeholder for v2 door/motion sensor | — | N | — |
| **REL-1** | Reliability | MTBF (ESP32 reboot cause: not crash) | ≥ 30 days between uncommanded reboots | Track `boot_cause` sensor; Grafana panel counts non-OTA reboots per 30d | M | A |
| REL-2 | Reliability | Recovery from cold power cycle | System fully operational (heartbeat + all sensors publishing) within 90 s of power restore | Scripted 12V kill/restore on bench; observe MQTT | M | A |
| REL-3 | Reliability | Broker outage tolerance | No firmware reboot while broker is down; reconnect within 120 s of broker return | Kill Mosquitto for 10 min | M | A |
| REL-4 | Reliability | WiFi outage tolerance | ESP32 does not reboot on WiFi loss; AIS TCP keeps serving local clients | Block SSID broadcast; verify stream_server still serves telnet | M | A |
| REL-5 | Reliability | UPS cutover | Zero data loss and no reboot on 12V → battery cutover | Bench script cycles 12V input while monitoring MQTT stream | M | H |
| REL-6 | Reliability | UPS runtime | ≥ 12 h at typical load (1.5–2 W) from full power bank with 12V removed | One-shot drain test on bench, log until brownout | M | M |
| **GLANCE-1** | Usability (at-a-glance) | Kelly assesses boat health | ≤ 3 seconds to decide "OK / not OK" from tablet card | Stopwatch test with 5 third-party subjects given the card cold | M | M |
| GLANCE-2 | Usability | Pete assesses full health | ≤ 15 seconds to identify any anomaly across 10 metrics | Same test pattern; Pete's full dashboard | S | M |
| GLANCE-3 | Usability | Helm display (underway) | Primary status readable from 1 m in direct sun | Photograph screen under simulated sun (4000 lux), assess contrast | S | M |
| GLANCE-4 | Usability | Day / night / red-mode toggle | Red-mode preserves night vision (no blue/white >5% luminance) | Inspect CSS in red theme; spectrophotometer optional | S | A |
| GLANCE-5 | Usability | No jargon in Kelly card | 100% plain-English labels (no "RSSI", "SoC", "MMSI") | Label audit checklist | M | M |
| **ALERT-1** | Alert delivery | Push reliability | ≥ 99% delivery over 30 days | HA `notify` log vs. phone receipt log | M | A |
| ALERT-2 | Alert delivery | Deduplication | No more than 1 push per alert per 1 h cool-down | Rapidly toggle condition 5× in 1 min; count pushes | M | A |
| ALERT-3 | Alert delivery | Silence control | "Mute 8 h" entity silences non-critical; bilge and anchor drag cannot be muted | Exercise mute; confirm bilge still fires | M | A |
| ALERT-4 | Alert delivery | Multi-channel escalation | Bilge → push + TTS + email within 30 s each | Inject; timestamp all three channels | M | A |
| ALERT-5 | Alert delivery | Alert under network partition | Offline event queues and fires on reconnect | Partition HA from broker; verify | S | A |
| **OBS-1** | Observability | Log retention on boat | ≥ 7 days of ESPHome logs available via API | Pull logs via ESPHome dashboard | S | M |
| OBS-2 | Observability | Metrics retention in HA | ≥ 90 days at 1-min resolution for all v1 entities | Query HA recorder; confirm coverage | M | A |
| OBS-3 | Observability | Long-term storage | InfluxDB retention ≥ 2 years (Phase 10) | Query retention policy | N | A |
| OBS-4 | Observability | Post-hoc debug | Any alert in last 30 days can be replayed with full context (sensor values ±10 min) | Pick 3 historical alerts, reconstruct | M | M |
| OBS-5 | Observability | Cloud relay logs | AIS relay logs last 30 days queryable | grep on OCI | S | M |
| **MAINT-1** | Maintainability | YAML-only firmware | 100% of ESPHome config is YAML; zero custom C++ lambdas over 20 lines | Line count audit | M | A |
| MAINT-2 | Maintainability | Reproducible setup | Fresh OCI VM + fresh ESP32 reach full operation from repo in ≤ 2 h | Dry-run provisioning on scratch VM | M | M |
| MAINT-3 | Maintainability | Secrets separated | No credentials in git; `secrets.yaml` gitignored; CI check blocks commits containing common secret patterns | Pre-commit hook + `gitleaks` scan | M | A |
| MAINT-4 | Maintainability | Config diffable | Every change visible in a PR; ESPHome compile check passes in CI | GitHub Action runs `esphome config` | M | A |
| **COST-1** | Cost | v1 BOM | ≤ $450 (target $405 per design §9) | Line-item spreadsheet | M | M |
| COST-2 | Cost | Ongoing cost | $0/mo (OCI Always Free, Let's Encrypt, no paid services) | Monthly bill review | M | M |
| COST-3 | Cost | No subscription lock-in | Zero mandatory paid dependencies for core function (aisstream is optional/free tier) | Design review | M | M |
| **PWR-1** | Power | Daily consumption | ≤ 5 Ah/day @ 12V typical | INA226 on ESP32 supply line over 48 h | M | A |
| PWR-2 | Power | UPS runtime | ≥ 12 h (see REL-6) | See REL-6 | M | M |
| PWR-3 | Power | Brownout ride-through | Ride 500 ms dip to 9 V without reboot (engine start) | Bench PSU dip script | M | H |
| **NET-1** | Network robustness | WiFi loss | No reboot; local AIS TCP continues | See REL-4 | M | A |
| NET-2 | Network robustness | DNS tampering (marina hijack) | Uses static 1.1.1.1; ignores DHCP DNS | `tcpdump` on DNS queries | M | A |
| NET-3 | Network robustness | LTE drop ≥ 5 min | System self-recovers; no stuck state | Toggle router WAN | M | A |
| NET-4 | Network robustness | AP fallback | AP mode after 5 min no known SSID | Block all known SSIDs | S | A |
| **SEC-1** | Security | MQTT TLS | All MQTT uses TLS 1.2+; no plaintext port exposed | `nmap` OCI VM | M | A |
| SEC-2 | Security | MQTT auth + ACL | Each device has unique creds; ACL restricts topics | Attempt cross-device publish with wrong creds | M | A |
| SEC-3 | Security | OTA authentication | OTA requires password; reachable only via VPN | Attempt OTA from WAN IP without VPN | M | A |
| SEC-4 | Security | Cert rotation | Let's Encrypt auto-renews ≥ 30 days before expiry | Check renewal cron logs | M | A |
| SEC-5 | Security | Physical tamper | Enclosure requires tool to open; no exposed USB on exterior | Visual inspection | S | M |
| **EXT-1** | Extensibility | Add sensor in <1 day | A new DS18B20 zone goes from plug-in to HA entity in ≤ 1 evening | Dry-run on bench | S | M |
| EXT-2 | Extensibility | Actuator hook (future) | Firmware scaffolding supports adding a `switch` component without schema rework | Design inspection | N | M |
| EXT-3 | Extensibility | NMEA2000 bridge path | Topic hierarchy can accept N2K-derived data without breaking subscribers | Design inspection | N | M |
| **PORT-1** | Data portability | History migration | HA DB + InfluxDB are exportable to CSV; ESPHome config is plain YAML in git | Export test | M | A |
| PORT-2 | Data portability | Hardware migration | Replace ESP32 with spare and restore via flash + config in ≤ 1 h, no data loss | Spare-swap drill | M | M |
| PORT-3 | Data portability | Cloud provider migration | OCI → Fly.io or Hetzner in ≤ 4 h via Ansible/Docker | Documented runbook; dry run on scratch | S | M |
| **TEST-1** | Testability | Virtual mode coverage | 100% of v1 entities have a virtual driver producing realistic values | Inventory check | M | A |
| TEST-2 | Testability | Integration test harness | Every alert path has an automated test that runs in CI | CI badge green | M | A |
| TEST-3 | Testability | Visual regression | Dashboard screenshots diff-gated in CI | Playwright `toHaveScreenshot` | S | A |

### A.3 Rationale by category

**Safety** is disproportionately weighted because a missed bilge alert can sink the boat. We demand both a positive test (alert fires) and a failure-mode test (alert fires despite broker outage). Fire is added via engine-compartment temperature; intrusion is deferred to v2 but the schema reserves the topic.

**Reliability** targets treat the system as a remote appliance: Pete cannot walk to the boat to reboot. MTBF is measured as uncommanded reboots, not power cycles. The 90-second cold-start target is aggressive but achievable with ESPHome's fast boot.

**At-a-glance usability** is the only category that demands human-in-the-loop testing: a stopwatch and five unfamiliar subjects for the Kelly card. The 3-second target comes from aviation HUD research — beyond 3 s, a glance becomes a read, and a read becomes a decision Kelly didn't want to make.

**Alert delivery** deduplication and mute semantics are critical because Kelly will physically turn the tablet face-down if it cries wolf. Bilge and anchor-drag are explicitly not muteable.

**Observability** distinguishes hot (7 days) from warm (90 days) from cold (2 years) retention, matching the debugging horizons Pete is likely to need.

**Maintainability** enforces the YAML-only discipline from design §11 — any drift to custom C++ is a smell.

**Cost** locks $0/mo ongoing; OCI policy change is in the risk register.

**Power** is generous at 5 Ah/day against a 300 Ah house bank but tightens future actuator budget.

**Network robustness** treats marina WiFi and DNS hijack as hostile; the hardcoded 1.1.1.1 is a specific mitigation.

**Security** is bare-minimum marine-practical: TLS, password, VPN-gated OTA. No 2FA, no hardware HSM.

**Extensibility**, **portability**, **testability** encode the "Pete can move this to a different boat in 2030" goal.

---

## B. Dashboard Design Principles

### B.1 At-a-glance patterns

- **Color by severity, never by type.** Green / amber / red map to OK / watch / act. No decorative blues.
- **Traffic-light states with explicit thresholds.** Every numeric tile has a defined green/amber/red range stored in HA `input_number` helpers so thresholds can be tuned without code.
- **One headline answer.** The Kelly card's top line answers "Is the boat OK?" in two words. Everything below is progressive disclosure.
- **Typography hierarchy.** 72 pt for the headline, 36 pt for primary metrics, 18 pt for context. Roboto or Inter, never serif.
- **No chart-junk.** Kelly's card has zero line charts. Pete's dashboard has sparklines, no grids, no legends unless two series overlap.
- **Progressive disclosure.** Kelly's card → "Details →" link to Pete's board → drill into historical graphs.
- **Minimum spatial cost.** Kelly's card fits on a 1024×600 tablet at arm's length without scroll.
- **Icon + text, never icon-only.** Icons are glanceable; text prevents misreads.

### B.2 Reference dashboards surveyed

| Source | Pattern to steal | Pattern to avoid |
|---|---|---|
| B&G Triton2 | Huge single-metric view; day/night toggle | Cramped multi-page navigation |
| Garmin GMI 20 | Sunlight-readable high-contrast | Fixed data set; not extensible |
| Victron VRM | Power-flow animation diagram; SoC ring | Dense on mobile; cloud-locked |
| Nobeltec TZ | Chart overlay density | Subscription model; unreadable at distance |
| OpenCPN | Free, extensible, data-honest | Ugly default skin; not glanceable |
| SignalK Kip | Theme-able, modular widgets, marine-native | Requires SignalK server (not in our stack) |
| Grafana-on-boat (open-boat-projects.org) | Good for Pete's deep view, time-series | Too dense for Kelly |
| Apple Weather | Headline + progressive detail | — |

### B.3 Three dashboards, three audiences

**B.3.1 Kelly Card ("How's My Boat")**
- Served on the kitchen tablet (Fully Kiosk Browser, always-on).
- Layout (top to bottom): status headline, power-source tile, house battery, bilge, three temperature tiles, "Details" link.
- Never shows a graph. Never shows a number without a color.
- Updates silently; alerts come via push + TTS, not card animation.
- Acceptance tested against GLANCE-1 (3 s to decide OK/not OK).

**B.3.2 Pete Dashboard (full expert view)**
- Browser on Pete's laptop / phone.
- Four-quadrant Lovelace: Power (shore/gen/battery + V/A/SoC), Environment (10-zone temps + humidity future), Position (map + AIS + anchor), Health (RSSI, uptime, heap, relay status, cert expiry).
- Sparklines on every numeric; tap-to-expand to full history.
- Includes debug strip: last 20 MQTT messages, last reboot cause, last OTA.

**B.3.3 Helm Display (underway at-a-glance)**
- Phase 10+, rendered on an ESP32-driven TFT at the nav station, or on a phone mounted at helm.
- Shows: speed over ground, heading, depth (future), AIS target count, battery V, wind (future), AIS transmit status.
- LVGL on ESP32-S3 with 3.5" TFT is the target. Fallback: tablet running HA dashboard with `helm` view.
- Red-mode CSS toggle driven by HA sun integration or manual button.

### B.4 Color palette

| Role | Day | Night | Red-mode |
|---|---|---|---|
| Background | `#F7F8FA` | `#0F1115` | `#000000` |
| Primary text | `#111418` | `#EDEEF1` | `#8B0000` |
| OK | `#1E8E3E` | `#34A853` | `#4A0000` (dim) |
| Watch | `#F29D0C` | `#F5B042` | `#6B0000` |
| Alarm | `#D93025` | `#F28B82` | `#B30000` |
| Accent (non-state) | `#1A73E8` | `#8AB4F8` | n/a |

Red-mode explicitly excludes blue channel >5% luminance to preserve dark adaptation.

### B.5 Iconography

Material Design Icons (MDI) only, piped through HA's stock icon system:
- `mdi:power-plug` (shore), `mdi:engine` (generator), `mdi:battery` (battery-only)
- `mdi:water-alert` (bilge wet), `mdi:water-off` (bilge dry)
- `mdi:thermometer` + color for temperatures
- `mdi:wifi-strength-*` for connectivity
- `mdi:anchor` for anchor modes
- `mdi:map-marker` for position

No emoji. No custom SVGs in v1.

---

## C. Dashboard Simulation & Visualization Without Hardware

Goal: Pete can iterate on every dashboard in this project before any ESP32 is flashed or sensor is wired.

### C.1 Layered simulation stack

| Layer | Purpose | Tool |
|---|---|---|
| 0. Static mockup | Early layout decisions | Figma / Excalidraw |
| 1. HA in Docker + virtual boat | Live Lovelace iteration | `homeassistant/home-assistant` container + `template` sensors |
| 2. MQTT replay | Realistic traffic patterns | `mosquitto_pub` feeding a broker from a JSONL file |
| 3. AIS replay | Exercise AIS path | AIVDM file via `nc` / Python to `stream_server` or directly to relay |
| 4. LVGL SDL simulator | Helm display preview on laptop | LVGL's native SDL target |
| 5. Wokwi for ESPHome | Firmware-in-browser | wokwi.com ESP32 + ESPHome compile |
| 6. Visual regression | Prevent dashboard drift | Playwright `toHaveScreenshot()` |
| 7. Storybook (if custom cards) | Component gallery | Storybook + `@storybook/web-components` |
| 8. Demo mode | Show system with canned data | HA `input_boolean.demo_mode` toggle |

### C.2 Layer 1 — Home Assistant in Docker with a fake boat

**Setup.** `docker-compose.yml` with Home Assistant + Mosquitto. A `virtual_boat/` package inside HA's `config/packages/` defines every v1 entity as a `template` sensor driven by `input_number` sliders and a master automation that nudges values on a realistic schedule.

**Value patterns.**
- House battery V: sine wave 12.3–13.8 V over 24 h with daily noise; drops to 12.0 V during simulated "engine start" events.
- Temperatures: diurnal cycle per zone (cabin 18–26 °C, engine 20 °C baseline with 80 °C spikes if "engine_running" flag, fridge 3–7 °C cycling).
- Bilge: 0 baseline, scheduled 30-second trip every 6 hours for alert testing.
- Power source: state machine cycling shore → battery → generator → shore over a demo day.
- RSSI: -55 to -75 dBm pink noise.

**Concretely.** An `automation` fires every 30 s running a `python_script` that writes realistic values. Or simpler: a `shell_command` that publishes JSON to MQTT, which HA ingests via MQTT discovery — this route also doubles as Layer 2's input.

**Acceptance.** Pete runs `docker compose up`, opens `http://localhost:8123`, and sees Kelly's card animating indefinitely. No ESP32 in the loop.

### C.3 Layer 2 — MQTT replay

**Format.** JSONL, one event per line: `{"t": 1713720000, "topic": "boat/hunter41/power/battery/house/v", "payload": "12.84", "retain": false}`.

**Producer.** A 30-line Python script reads JSONL, sleeps `t_i+1 - t_i` real seconds (or scaled faster for dev), calls `paho.mqtt` publish. Source recordings come from: the virtual-boat (Layer 1) logging itself, or eventually a real on-boat capture.

**Consumer.** Same Mosquitto broker HA is subscribed to. Dashboards animate as if live.

**Scale knob.** A `--speed 60x` flag lets Pete compress 24 h into 24 min for demos.

### C.4 Layer 3 — AIS replay

**Source data.**
- Open AIVDM datasets: NOAA AIS historical, AISHub samples, or the small bundled samples in `gpsd` (`test/daemon/AIVDM*.log`).
- Norwegian Coastal Administration publishes public AIS samples.
- Or record a 30-minute pcap at any working AIS receiver.

**Replay methods.**
- To exercise `stream_server`-side consumers: `nc -l 6638 < sample.aivdm` on Pete's laptop; point OCI relay at laptop.
- To exercise relay → aisstream path: a Python script that opens a TCP listener and time-cadences lines out to simulate the ESP32.
- Provide a `--loop` flag so it runs indefinitely for demos.

**Acceptance.** OCI relay ingests replayed stream; aisstream test MMSI appears in Pete's future app. No ESP32 involved.

### C.5 Layer 4 — LVGL SDL simulator for helm display

**What.** LVGL supports a desktop simulator target (SDL2) that renders the exact same UI code you'd flash to an ESP32-S3 + TFT. Pete develops the helm display on his PC against mock data sources.

**How.**
1. Clone `lv_port_pc_eclipse` or `lv_port_pc_vscode` from the LVGL org.
2. Port the helm display code; feed data via a local function that reads MQTT from Layer 2.
3. Run `make && ./demo` → a window appears on the desktop with the live dashboard.

**Benefit.** Kelly can sit at the kitchen table and tell Pete the fonts are too small before he orders a panel.

### C.6 Layer 5 — Wokwi for ESPHome

**What.** Wokwi.com simulates ESP32 silicon in the browser. It integrates with ESPHome (via `wokwi-esp32` board and the Wokwi CLI / VS Code extension).

**How.**
1. Add a `wokwi.toml` and `diagram.json` to the ESPHome project.
2. `wokwi-cli` compiles and boots the firmware in a virtual chip.
3. The simulated ESP32's WiFi can bridge to the local Docker network, hitting the same Mosquitto broker as Layer 1.

**Limits.** No dAISy, no real UART data. For AIS, inject AIVDM via a Wokwi-simulated serial device (supported).

**Acceptance.** CI runs a Wokwi smoke test on every PR: firmware boots, WiFi connects, first MQTT publish arrives within 30 s.

### C.7 Layer 6 — Visual regression

**Tool.** Playwright in headless Chromium. Free, no Percy/Chromatic subscription.

**Flow.**
1. Docker compose brings up HA + Mosquitto + virtual boat at known-seeded state (freeze all randomness via an `input_number.random_seed`).
2. Playwright logs in, navigates to each dashboard, calls `expect(page).toHaveScreenshot('kelly-card.png')`.
3. CI fails the PR if any screenshot diffs beyond tolerance.
4. Baseline screenshots live in git under `test/screenshots/`.

**Coverage.** Minimum: Kelly card day, Kelly card night, Pete dashboard, helm view. Add one test per alert state (bilge wet, battery low, offline).

### C.8 Layer 7 — Storybook (only if custom Lovelace cards are built)

**Trigger.** Only needed if v1's built-in cards (entities, glance, conditional, picture-entity, markdown) prove insufficient. Prefer stock cards to custom.

**If needed.** Storybook with `@storybook/web-components` hosts each card variant. Each variant has a `*.stories.ts` with mocked `hass` objects covering every state (OK/watch/alarm/unavailable).

### C.9 Layer 8 — Demo mode in production

**Why.** Pete may want to show the system at a yacht club talk or to a prospective buyer without exposing live boat data.

**How.** An `input_boolean.demo_mode` in HA, when true, switches every sensor binding to its virtual counterpart via a `template` wrapper. The real MQTT entities keep running in the background; the dashboards just read from templates that check the flag.

**Safety.** Disable alert automations while demo_mode is on — alerts refer to demo values only, routed to a logger, not to push.

### C.10 How the layers chain together

```
                           ┌────────────┐
 recorded real AIS  ──────►│ Layer 3    │─┐
                           └────────────┘ │
                                          ▼
 seeded fake values ─────► Layer 1 ─► MQTT broker ─► Home Assistant ─► Lovelace
                                          ▲                              │
 JSONL replay ───────────► Layer 2 ───────┘                              │
                                                                         │
 Wokwi ESP32 (Layer 5) ──────────────────►┘                              │
                                                                         ▼
                                              Playwright (Layer 6) ─► baseline diffs
                                                                         │
                                              LVGL SDL (Layer 4) ◄───────┘ (shared MQTT)
```

### C.11 Recommended initial build order

1. Docker compose with HA + Mosquitto (1 evening).
2. Virtual-boat package with all v1 entities (1 evening).
3. Draft Kelly card + Pete dashboard against virtual data (1 weekend).
4. Playwright screenshot baseline (1 evening).
5. AIS AIVDM replay script (half day).
6. Wokwi smoke test in CI (half day).
7. LVGL SDL only when helm display work begins (Phase 10+).

This entire stack is buildable with zero boat hardware and takes ~2 weekends.

---

## D. User Stories

1. **As Kelly**, I want to glance at the kitchen tablet and know in 3 seconds whether the boat is OK, so that I don't have to ask Pete or learn jargon.
2. **As Kelly**, I want my phone to buzz loudly if the bilge is taking on water, so that we can act even if we're away from home.
3. **As Kelly**, I want to mute non-critical alerts for 8 hours when I'm trying to sleep, so that a low-battery notice doesn't wake me but bilge still would.
4. **As Pete**, I want a single dashboard with all sensor values and sparklines, so that I can diagnose a problem in one screen before calling the marina.
5. **As Pete**, I want to SSH into nothing — every deploy is a git push and a CI build, so that there are no "what did I change last time" mysteries.
6. **As Pete**, I want to OTA-update firmware from my laptop at home, so that I don't drive 90 minutes to Sandusky for a config tweak.
7. **As Pete**, I want every alert to have a paired automated test, so that refactors don't silently break safety paths.
8. **As Pete**, I want the dashboard to work fully in a Docker container on my laptop with no boat, so that I can iterate on the UI in winter storage.
9. **As Pete**, I want to replace the ESP32 with a spare in under an hour with no history loss, so that a dead board is a nuisance, not a project.
10. **As Kelly and Pete**, we want a single "demo mode" toggle that shows canned values, so that we can demo the system to friends without exposing our live data.

---

## E. Acceptance Criteria for v1 (Phases 1–6)

Each phase's exit gate restated as explicit checks. A phase is "done" when every M-priority box is ticked.

### Phase 1 — Bench prototype (AIS → local TCP)
- [ ] M — `telnet <esp32-ip> 6638` shows ≥ 1 AIVDM line per minute under a working antenna.
- [ ] M — OpenCPN ingests TCP stream and displays ≥ 1 target within 10 min.
- [ ] M — ESPHome config is checked into git with a CI `esphome config` step that passes.
- [ ] S — RSSI and uptime publishing to HA's local test MQTT.

### Phase 2 — Cloud infrastructure
- [ ] M — OCI ARM VM provisioned via Terraform or documented `oci-cli` script.
- [ ] M — Mosquitto serves TLS on port 8883 with a Let's Encrypt cert; `openssl s_client` verifies.
- [ ] M — Python AIS relay is a systemd service with `Restart=always` and logs to journald.
- [ ] M — WireGuard tunnel OCI ↔ Pete's home passes `wg show` + `ping` test.
- [ ] M — HA subscribes to OCI broker, receives bench ESP32 heartbeat.
- [ ] M — Test MMSI appears on aisstream contributor dashboard within 15 min.
- [ ] S — OCI relay logs archived to object storage bucket ≥ 30 days.

### Phase 3 — Hardened core platform
- [ ] M — All components mount in Polycase WC-23F with ≥ 10 mm clearance.
- [ ] M — 12V input fused, TVS-protected, reverse-polarity protected per §10.
- [ ] M — 72-hour bench soak with zero uncommanded reboots (REL-1 partial).
- [ ] M — Five simulated 12V-cut cycles; zero data loss (REL-5).
- [ ] M — OTA from laptop via simulated WireGuard completes in < 2 min.
- [ ] M — Pass-through power bank verified simultaneous charge+discharge on bench with USB-C PD load tester.
- [ ] M — 12-hour UPS runtime test passes from full bank (PWR-2 / REL-6).
- [ ] S — Enclosure passes hose-down test (IP66 claim).

### Phase 4 — Boat install + connectivity
- [ ] M — Unit mounted in nav station or dry locker, all cables strain-relieved (NF-5).
- [ ] M — 12V feed from house bank with fuse at source (ABYC).
- [ ] M — ESP32 joins onboard LTE router (BoatNet5G) with static DHCP lease.
- [ ] M — AIS visible on aisstream ≥ 10 targets within first 4 hours at slip.
- [ ] M — MQTT heartbeats arrive every 60 ± 5 s for 24 h.
- [ ] M — Kelly's card shows "Boat ONLINE" (GLANCE-1 smoke).

### Phase 5 — Core sensors
- [ ] M — 3× DS18B20 report within ±1 °C of a calibrated reference.
- [ ] M — INA226 house-bank voltage matches a DVM within 0.05 V.
- [ ] M — Starter-battery divider reads within 0.1 V (calibration allowed).
- [ ] M — Shore + generator opto-isolators each correctly detect AC presence across a test outlet (toggle test, 100% correct over 20 cycles).
- [ ] M — Kelly's card fully populated with every tile green under normal conditions.
- [ ] M — Historical graphs in HA show 24 h of 1-minute data (OBS-2 partial).

### Phase 6 — Critical alerts
- [ ] M — Bilge trip → push within 30 s p95 (SAFE-1).
- [ ] M — Bilge trip during simulated broker outage → push within 60 s of broker recovery (SAFE-2).
- [ ] M — Offline > 15 min → push (SAFE-3).
- [ ] M — House battery < 11.8 V sustained 5 min → push, single not repeated (SAFE-4, ALERT-2).
- [ ] M — Shore-power loss → push to Pete only (not Kelly) during weather condition.
- [ ] M — 14-day soak with zero false-positive alerts across all rules.
- [ ] M — All alert paths have automated CI tests (TEST-2).
- [ ] M — Mute 8 h input silences low-battery but NOT bilge (ALERT-3).

**v1 ship gate:** All Phase-1-through-6 Must-have items ticked; all Safety-category Must-haves across all phases ticked.

---

## F. How This Plugs Into TDD

A parallel research track is defining the test architecture. This rubric is designed to hand that track ready-to-implement test cases. Each criterion's **Test** column tells the TDD track whether it's automated (A), manual (M), or hybrid (H).

### F.1 Automated (A) — live in CI

Every `A` criterion has one of:
- **Unit test** (pytest) around a Python helper — e.g., the relay's reconnect logic.
- **ESPHome compile test** (GitHub Action, `esphome config *.yaml`).
- **Integration test** (docker-compose stack: HA + Mosquitto + virtual boat + Playwright) that exercises the rule and asserts the resulting MQTT/HA state within a time budget.
- **Visual regression test** (Playwright `toHaveScreenshot`) for layout criteria.

### F.2 Manual (M) — in the commissioning checklist

Every `M` criterion goes into `docs/commissioning-checklist.md` with the exact measurement procedure and a pass/fail row. Examples: GLANCE-1 (human stopwatch test), PWR-2 (12-hour UPS drain), MAINT-2 (fresh-VM provisioning dry run).

### F.3 Hybrid (H) — partially automated

E.g., SAFE-1 bilge latency: the firmware side is automated (virtual button press), but the phone receipt timestamp requires either a manual reading or a dedicated notifier-to-webhook round-trip (recommended: build a small webhook receiver that logs push delivery and lets the test assert latency).

### F.4 Virtual vs integration modes

TDD architecture should expose two test modes (per the "virtual or integration modes" note):
- **Virtual mode:** No hardware. Uses Layers 1–5 from §C. Runs on every PR.
- **Integration mode:** Real ESP32 on a bench rig with simulated sensors (relays, resistor substitution for thermistors, a 555-based AIS-like UART signal). Runs nightly or pre-release.

Each criterion should declare which mode(s) validate it. Safety criteria must pass in **both** modes before v1 ship.

### F.5 Criteria → test file mapping (proposed)

| Criterion | Test file |
|---|---|
| SAFE-1, SAFE-2, SAFE-3 | `tests/integration/test_alerts.py` |
| REL-2, REL-3, REL-4 | `tests/integration/test_resilience.py` |
| GLANCE-1..5 | `tests/manual/commissioning-checklist.md` + `tests/visual/test_dashboards.spec.ts` |
| ALERT-* | `tests/integration/test_alert_delivery.py` |
| MAINT-1, MAINT-4 | `.github/workflows/ci.yaml` (lint + esphome config) |
| NET-1..4 | `tests/integration/test_network_loss.py` (uses `iptables` in docker) |
| SEC-1, SEC-2, SEC-3 | `tests/security/test_tls_and_auth.py` |
| TEST-1, TEST-3 | `tests/visual/*.spec.ts` |
| PWR-1..3 | `tests/manual/commissioning-checklist.md` |

---

## G. Open Questions for Pete

1. **Alert channels priority.** Is SMS required as a fallback, or are Pushover / HA Companion + email sufficient? SMS requires Twilio (costs >$0/mo), which violates COST-2.
2. **Helm display v1 vs. deferred.** Do you want an LVGL helm panel as part of Phase 10, or is a phone-at-helm acceptable indefinitely? Affects whether we invest in Layer 4 simulation now.
3. **Kelly threshold authority.** Should Kelly be able to tune her own card's green/amber thresholds, or does Pete own those numbers? Affects whether we expose `input_number` helpers on the Kelly view.
4. **Demo mode priority.** Is this truly stretch, or do you want it in v1 for your yacht-club talk? Non-trivial template-wrapping work.
5. **Visual regression noise tolerance.** What pixel-diff percentage counts as a break? Defaults to 0.2% but marine UIs with live data may need 1% + masking of time strings.
6. **Kelly card location(s).** Kitchen tablet only, or also her phone's lock-screen widget? A widget is a separate integration (HA Companion iOS/Android widgets).
7. **Sun/red-mode trigger.** Manual button, HA sun integration, or both? Red-mode is only useful on a boat-mounted display, not the kitchen tablet.
8. **AIS-TCP local-bridge consumers.** Any planned on-boat TCP consumer (OpenCPN on a Pi at the nav station)? Affects whether we keep NET-4 (AP fallback) as M or S.
9. **Post-deploy screenshot golden.** Should the production dashboard update its own visual-regression baseline automatically after a human-approved change, or is baselining strictly a pre-merge step?
10. **Sign-off process.** Who signs each phase's exit gate — Pete alone, or Pete + Kelly on the Kelly-facing criteria (GLANCE-1, ALERT-3)?

---

*End of evaluation criteria & dashboard simulation plan v1.0.*
