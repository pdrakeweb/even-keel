# EvenKeel — Phased Implementation Roadmap

**Supersedes:** `research/sailboat-monitor-design.md` § 13.
**Style:** Each phase delivers working end-to-end functionality; Pete can stop at any phase with a useful, shippable system. Every phase has (a) deliverables, (b) acceptance tests in Gherkin, (c) exit criteria, (d) estimated effort.

The two biggest changes vs. the prior phase plan:

1. **Test harness is Phase 0**, before any other work. Every subsequent phase writes its Gherkin scenarios first and gates the phase on them passing in virtual mode at minimum.
2. **Cloud infrastructure is gone.** The prior "Phase 2 — Cloud Infrastructure" is replaced by **Phase 2 — Home & Boat Hosting** (HA Green + Pi 4 + WireGuard). No OCI.

---

## Phase 0 — Test Harness Scaffold *(new)*

**Goal:** Nothing compiles for the firmware yet, but the test machinery does.

**Work:**
- Create `tests/` directory per [`tdd-architecture.md §D`](tdd-architecture.md).
- Scaffold `pytest-bdd`, `aiomqtt`, `pytest-playwright`, Wokwi CLI config.
- `docker-compose.yml` running Mosquitto + Home Assistant (with a minimal seed config).
- `adapters/virtual.py` skeleton wiring to Docker-mqtt and a stub Wokwi adapter.
- First passing scenario: `Feature: Test harness self-check — Scenario: MQTT round-trip`.
- GitHub Actions workflow running the virtual suite on every push.

**Exit:** Green CI badge on a trivial "publish + receive MQTT" test.
**Effort:** 1 weekend.
**Cost:** $0.

---

## Phase 1 — Bench AIS Prototype

**Goal:** Prove AIS reception on the bench; exercise the Wokwi + ESPHome flow end-to-end.

**Hardware:** M5Atom (existing) or one ESP32-S3-DevKitC-1 + dAISy HAT + desktop VHF whip.
**Software:** Minimal `firmware/boat-mon.yaml`: `uart` + `stream_server` + `web_server v3`. WiFi to home network (home broker not yet needed).

**Key Gherkin scenarios:**
```gherkin
Scenario: Local AIS TCP stream receives sentences
  Given BoatMon-1 is running the Phase 1 firmware
  And an AIVDM sample is replayed into the dAISy UART at 38400 baud
  When a client connects to TCP port 6638
  Then the client receives at least 10 valid AIVDM sentences within 30 seconds
```

**Verify:** `telnet <esp32-ip> 6638` shows live AIS NMEA; OpenCPN loads boat's TCP stream.
**Exit:** AIS streaming on Pete's desk + matching Gherkin scenario green in virtual mode (Wokwi UART replay).
**Effort:** 1–2 evenings.
**Cost:** existing M5Atom or +$15 for ESP32-S3; dAISy $75 (already planned).

---

## Phase 2 — Home & Boat Hosting *(replaces prior OCI phase)*

**Goal:** Stand up infra (no cloud). Complete the broker + HA + WireGuard story.

**Work:**
- Home Assistant Green arrives; flash HA OS (default); configure admin user + MFA.
- Install Mosquitto add-on on HA Green; create `pete-user`, `home-bridge`, device-specific users.
- Stand up WireGuard on home router (server) with Pete's phone as a client.
- Provision Raspberry Pi 4 4GB + USB SSD on the bench; install HA OS; install Mosquitto add-on (client role; bridge to home once tunnel is up).
- Configure LetsEncrypt DNS-01 against Pete's domain; issue cert for `boat-broker.peteskrake.com` and `home-broker.peteskrake.com`.
- Set up Git repo for HA config on home side; commit hook on every `/config` change.
- **On-boat Pi not yet on the boat** — bench staging only.

**Key Gherkin scenarios:**
```gherkin
Scenario: Home HA bridges to boat broker over simulated WireGuard
  Given the test docker-compose brings up home-mosquitto and boat-mosquitto with a bridge
  When a publisher pushes to "boat/hunter41/test/heartbeat" on the boat broker
  Then within 5 seconds the home broker retains the same payload
  And home HA has created an entity reflecting it
```

**Verify:** Pete's phone can access home HA dashboard via WG tunnel. Bench-staged Pi Mosquitto bridges to home broker cleanly.
**Exit:** MQTT round-trip from the bench ESP32 to HA Green via the bench Pi bridge.
**Effort:** one weekend.
**Cost:** HA Green $99 + Pi 4 kit $75 + SSD $20 = **$194**.

---

## Phase 3 — Hardened Core Platform *(simplified)*

**Goal:** Build the actual boat-ready BoatMon-1 unit. Per [simplicity-review.md](simplicity-review.md), this phase is now an evening of plug-together work instead of a weekend of soldering.

**Work:**
- **Adafruit ESP32-S3 Feather + Featherwing proto** in an off-the-shelf Feather-sized IoT enclosure.
- One soldering session (~15 joints) on the Featherwing proto: 3-wire dAISy UART, 2-wire bilge float, 3-wire Tier 0 LED + buzzer, 4.7 kΩ 1-Wire pullup, 3× DS18B20 lead terminals.
- **Power: one USB-C panel-mount jack.** Separately, install a Scanstrut ROKK Charge+ USB-C outlet in the nav station wired to house 12V. Done.
- **Sensors all plug in** via STEMMA QT cables. No I²C soldering.
- **AC detection: 2× Shelly Plus Plug S** — one on shore inlet, one on generator outlet. Both publish via MQTT. No AC wiring in the boat-node enclosure.
- **Direct-from-boat Pushover notification** configured in ESPHome for the home-independent safety path.
- ESPHome `web_server v3` with `local: true` for Tier 2 phone dashboard.
- OTA password; test OTA from Pete's laptop via WG tunnel.

**Verify:** 72-hour bench soak. Simulate power cuts on the USB-C line. Confirm OTA works.
**Exit:** Unit ready for boat install; all @phase3 scenarios green in HIL mode.
**Effort:** one evening build + 72 h soak (was: full weekend + soak).
**Cost:** Feather + proto + sensors + enclosure + Shelly plugs + Scanstrut ≈ **~$235** (see simplicity-review.md §4).

**Key Gherkin scenarios:**
```gherkin
Scenario: Tier 0 buzzer fires on bilge wet
  Given BoatMon-1 is running in live-integration test mode
  When the bilge sensor is injected as "wet" for 10 seconds
  Then within 2 seconds GPIO for the buzzer is asserted
  And within 30 seconds Home Assistant entity "binary_sensor.boatmon_bilge_water" is "on"

Scenario: Power-cycle recovery
  Given BoatMon-1 has been publishing telemetry
  When boat 12V is removed for 30 seconds and restored
  Then within 90 seconds all entities re-populate in HA from retained topics
```

**Verify:** 72-hour bench soak. Simulate engine-start transients. Confirm OTA works via WG-simulated tunnel.
**Exit:** Unit ready for boat install; all @phase3 scenarios green in HIL mode.
**Effort:** full weekend + 72h soak.
**Cost:** enclosure + power + connectors ≈ **$180**.

---

## Phase 4 — Boat Install + Connectivity

**Goal:** Mount on the Hunter. Establish operating connectivity.

**Work:**
- Install BoatMon-1 in nav station or dry locker.
- 12V feed from house bank with fuse at source per ABYC.
- AIS antenna (splitter off existing VHF vs dedicated — decide at install time per mast/rigging inspection).
- Install boat Pi in same locker; configure WG client outbound to home router.
- ESP32 joins boat WiFi; publishes to boat broker; boat broker bridges to home broker.
- ESPHome `web_server` Tier 2 dashboard bookmarked as PWA on Pete and Kelly's phones.
- Fallback AP `BoatMon-Fallback` tested by turning off LTE router.

**Key Gherkin scenarios:**
```gherkin
Scenario: Boat visible from home HA via WireGuard
  Given BoatMon-1 is installed at the slip and LTE router is up
  When 60 seconds elapse
  Then home HA shows "binary_sensor.boatmon_online" as "on"
  And aisstream-bound TCP stream is reachable at boat-broker.peteskrake.com:6638 via WG

Scenario: Crew phone can reach Tier 2 dashboard
  Given a phone is on the boat WiFi
  When the crew opens http://boatmon-1.local/
  Then the ESPHome web_server page loads within 5 seconds
```

**Verify:** AIS visible in OpenCPN-at-home via WG tunnel. MQTT heartbeats in HA. Kelly's card (bare version) shows "ONLINE".
**Exit:** Boat reporting from the marina.
**Effort:** 1 day install + commissioning.
**Cost:** $0 new hardware (everything from prior phases).

---

## Phase 5 — Core Sensors

**Goal:** Meaningful boat health in HA.

**Hardware added:** 3× DS18B20 (cabin / engine / fridge), INA226 (house bank), voltage divider (starter), 2× opto-isolators (shore + gen), BME280 (cabin humidity + baro), optional SHT40 for mold-risk monitoring.

**Key Gherkin scenarios:**
```gherkin
Scenario: Cabin temperature updates within 60 seconds
  Given BoatMon-1 is installed with DS18B20 on the cabin probe
  When the probe is heated from 22°C to 26°C
  Then within 60 seconds entity "sensor.boatmon_cabin_temp" reports ≥26.0

Scenario: Shore power detection
  Given shore power is disconnected
  When shore is plugged in
  Then within 30 seconds entity "binary_sensor.boatmon_shore_power" is "on"
```

**Verify:** All values reasonable; historical graphs tracking.
**Exit:** Kelly's "How's My Boat" card fully populated.
**Effort:** 1 day install.
**Cost:** sensors ≈ **$80**.

---

## Phase 6 — Critical Alerts *(MVP v1 ships here)*

**Goal:** Safety coverage via HA automations. At Phase 6 exit, **v1 is shippable**.

**Hardware:** bilge float switch wired to GPIO. Nothing else new.
**Software:** HA automations — bilge, low battery, offline watchdog, shore-lost, generator-start events. Push (HA Companion), TTS (Google Cast), email (SMTP integration — Pete's own outbound via his own server or provider — NO subscription). Tier 0 buzzer driven from GPIO directly.

**Key Gherkin scenarios (several already listed in tdd-architecture.md):**
```gherkin
Scenario: Bilge alarm delivers push + TTS + email within 30 seconds
  ...

Scenario: Offline watchdog fires after 15 minutes silent
  Given BoatMon-1 has been online for 1 hour
  When BoatMon-1 goes silent for 16 minutes
  Then Pete receives a push notification containing "Boat offline"
  And Kelly does NOT receive a notification within 30 minutes

Scenario: Low-battery alert with hysteresis
  Given house battery is 12.8 V
  When the battery falls to 11.7 V for 6 minutes
  Then Pete and Kelly receive a push containing "Low battery"
  And when the battery recovers to 12.2 V no second alert fires
```

**Verify:** Manually trigger each alert; confirm delivery over all channels. 14-day soak with no false positives.
**Exit:** All alerts proven in live-integration mode.
**Effort:** half day + tuning.
**Cost:** **$0** — all software except the $25 float switch (already in Phase 3 if Pete wired it).

---

## Phase 7 — Victron BLE Telemetry

**Goal:** High-resolution battery data without new wiring.

**Prereq:** Victron SmartShunt installed (likely part of Pete's electrical upgrade).
**Hardware:** none (ESP32-S3 has BLE).
**Software:** `Fabian-Schmidt/esphome-victron_ble` external component; pair via MAC + bindkey.

**Key Gherkin scenarios:**
```gherkin
Scenario: Victron SmartShunt values stream to HA
  Given the SmartShunt is reporting 78% SoC and -3.2A discharge
  When BoatMon-1 has been running for 30 seconds
  Then entity "sensor.boatmon_house_soc" reports 78 ±1
  And entity "sensor.boatmon_house_current" reports between -4.0 and -3.0
```

**Verify:** All SmartShunt values match Victron app; HA history matches reality over a charge/discharge cycle.
**Effort:** 2–3 hours.
**Cost:** $0 firmware; SmartShunt ~$170 one-time.

---

## Phase 8 — GPS + Tank Levels

**Goal:** Position + fluid inventory.

**Hardware:** u-blox NEO-M9N on UART2 + active antenna; ADS1115 ADC tapped off tank senders.
**Software:** `gps:` component; per-tank calibration lookup tables.

**Key Gherkin scenarios:**
```gherkin
Scenario: GPS position available within 60 seconds of cold start
  Given BoatMon-1 is cold-started at the slip
  When 60 seconds pass (warm antenna)
  Then entity "sensor.boatmon_latitude" is within 5 m of the known slip lat
  And entity "sensor.boatmon_longitude" is within 5 m of known slip lon

Scenario: Fuel tank reading tracks sender resistance
  Given the fuel sender is set to simulate 75% full (resistance value X)
  When the ADS1115 updates
  Then entity "sensor.boatmon_fuel_pct" reads 75 ±2
```

**Verify:** GPS within 5 m; tanks match dipstick.
**Effort:** one weekend (tank calibration = the time sink).
**Cost:** GPS module + antenna ≈ $65; ADS1115 $15.

---

## Phase 9 — Anchor Drag + Slip Breakaway

**Goal:** Location-aware safety.

**Hardware:** none (GPS from Phase 8).
**Software:** HA automations:
- **Slip mode (always armed):** geofence around Safe Harbor Sandusky slip. Alert on leave.
- **Anchor mode (manual arm):** alert if position >50 m from armed point OR speed >0.5 kt sustained 2 min.

**Key Gherkin scenarios:**
```gherkin
Scenario: Slip breakaway alert
  Given slip-mode geofence is armed at lat/lon X,Y with 30m radius
  When the GPS track moves to 50 m from X,Y for 2 minutes
  Then Pete and Kelly receive a critical push notification containing "Boat has left slip"

Scenario: Anchor drag alert
  Given anchor-mode is armed at current position with 50m radius
  When GPS track drifts 60 m for 3 minutes
  Then Pete receives a critical push notification
  And Kelly receives a critical push notification
```

**Verify:** 14-day soak at slip without false positives. Simulate breakaway by moving armed point in HA.
**Effort:** half day.
**Cost:** $0.

---

## Phase 10 — Full Dashboard + Expanded Temperature Coverage

**Goal:** Complete telemetry; Pete's full HA dashboard.

**Hardware added:** 7 more DS18B20 on the 1-wire bus (star topology + pullup, split to a second bus if >5 m total).

**Software:**
- Full Pete HA dashboard: graphs, trend cards, 10-zone temperature map, AIS target list.
- InfluxDB add-on (optional) for multi-year retention.

**Effort:** one weekend for the dashboard.
**Cost:** 7× DS18B20 ~$56 = **~$56**.

Note: The on-boat **Tier 1 LVGL panel** has been deferred to Phase 11+ per resolved Q18. v1 through Phase 10 ships with Tier 0 LED+buzzer + Tier 2 phone PWA only.

---

## Phase 11+ — Stretch Goals

### Phase 11a — N2K Read (Tier 6, DIY) [~1 weekend, ~$60]

Add a dedicated CAN-ESP32 satellite that taps the N2K backbone via tee + drop cable, decodes 5–10 PGNs (lat/lon, COG/SOG, depth, wind, engine RPM, water temp), and publishes to MQTT under the canonical topics in [`nmea2000-integration.md §11`](nmea2000-integration.md). **Prerequisite:** Q40–Q43 resolved at survey (does the boat have N2K, what era, what connector). **Net:** Phase 8's $70 GPS hardware becomes optional — chartplotter's GPS is now in HA for free.

### Phase 11b — SignalK upgrade (Tier 6, commercial) [~1 day, ~$185 add'l]

If/when Path A's hand-rolled decoder list grows painful, swap to a Yacht Devices YDNU-02 USB-N2K gateway plugged into the on-boat Pi running SignalK Server. SignalK normalizes the data and republishes to MQTT — same topics, no HA dashboard changes required. Bonus: free SignalK Kip dashboard for an additional on-boat browser-based view.

### Phase 11c — NMEA 0183 (legacy talkers) [optional, ~$5–125]

Only if a survey reveals 0183-only talkers (DSC VHF, older autopilot, fluxgate). Adds a second software UART on BoatMon-1 reading from a multiplexer via MAX3232 adapter.

### Other Phase 11+ candidates

- **On-boat Tier 1 LVGL panel** (Waveshare ESP32-S3-Touch-LCD-4.3 or 5"). Dashboard head at nav station. ~$55 + enclosure. Adds `firmware/dashboard-head.yaml`, LVGL SDL simulator in test harness, Phase-10-style visual-regression Gherkin scenarios. **Combine with Phase 11a:** the Touch-LCD-4.3B board has CAN onboard, so Tier 1 panel + N2K read can share one device.
- Continuous bilge level (JSN-SR04T ultrasonic).
- **Actuators** with safety interlocks: bilge blower, cabin fan, Webasto/Espar diesel heater enable line. Mechanical kill switch in series. **No AC resistive heater actuation** — refused by design.
- Engine RPM via alternator-W tap (only if N2K not available — otherwise use Phase 11a).
- Wind / barometric sailing instruments (only if N2K not available — otherwise use Phase 11a).
- Victron VE.Direct ingestion (Tier 6c) for solar MPPT or Phoenix inverter (~$8 cable + adapter).
- Modbus RTU ingestion (Tier 6d) for any industrial sensor on the boat (~$3 MAX485 adapter).
- Redundant safety-only ESP32 (independent watchdog).
- Inkplate 6 e-ink "always-on quiet mode" display above companionway.
- Twilio SMS alert channel as an opt-in HA integration for users who already carry a Twilio subscription.

Each of these is self-contained and follows the same Gherkin-first pattern.

---

## Cost Roll-up

| Phase group | Marginal $ | Cumulative |
|---|---|---|
| Phase 0 (test harness) | 0 | 0 |
| Phase 1 (bench AIS) | ~95 (dAISy+ESP32) | 95 |
| Phase 2 (hosting: HA Green + Pi 4 + SSD) | 194 | 289 |
| Phase 3 (hardened core: enclosure + connectors + simplified USB-C power — no UPS) | ~130 | 419 |
| Phase 4 (install only; $0 new) | 0 | 419 |
| Phase 5 (core sensors) | 80 | 499 |
| Phase 6 (software-only + bilge float $25 if not done) | 25 | 524 |
| **v1 ship gate (Phase 6)** | — | **~$524** |
| Phase 7 (Victron BLE; SmartShunt if not owned: +170) | 0 or 170 | 524–694 |
| Phase 8 (GPS + tanks) | 80 | 604–774 |
| Phase 9 (software only) | 0 | 604–774 |
| Phase 10 (full dashboard + 7×DS18B20; no LVGL panel) | 56 | 660–830 |
| **Full Phase 1–10 build** | — | **~$660–830** |
| Optional: Anker 733 pass-through UPS | +110 | — |
| Optional: Phase 11+ Tier 1 LVGL panel | +75 | — |

No ongoing costs. Zero subscriptions.

---

## Timing Shape

If Pete spends 1–2 weekends per phase, the path from today to v1 ship is **~6–8 weekends**, plus 14 days of soak at Phase 6 exit. Phases 7–10 can stretch over a season as Pete sails and learns what matters.
