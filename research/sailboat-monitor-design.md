# Sailboat Monitoring & AIS Gateway — Architectural Design

**Project:** Single-ESP32 boat telemetry and AIS receiver/forwarder, with Home Assistant integration and cloud-hosted AIS relay.
**Target vessel:** Hunter 41DS (pending purchase), Safe Harbor Sandusky, Lake Erie.
**Document version:** 1.0 — April 2026
**Status:** Design locked for v1; ready to begin Phase 1.

---

## 1. Executive Summary

A single ESP32-S3 node on the boat ingests AIS from a Wegmatt dAISy HAT and telemetry from a catalogue of marine sensors, then publishes both to the outside world over WiFi only. Connectivity on the water is provided by an existing 4×4 MIMO X75 cellular router; in port, by the same router or marina WiFi (multi-SSID priority-based selection). AIS is pushed to aisstream.io via a small relay running on Oracle Cloud's Always Free tier. Sensor telemetry flows via MQTT-over-TLS to a Mosquitto broker on the same OCI VM, with Home Assistant at home as the subscriber and long-term data store. Kelly gets a minimal "How's My Boat" card in HA's Lovelace UI for always-on tablet display.

**Design priorities:**
1. Reliability under marine conditions (heat, vibration, humidity, transients).
2. No dependence on home network reachability for data to flow.
3. ESPHome YAML-only firmware — minimal custom code.
4. Commercial, replaceable parts; no custom PCBs.
5. Phased deployment where each phase delivers working end-to-end functionality.

---

## 2. Goals, Stretch Goals, Non-Goals

### Primary Goals (v1)
- Reliable AIS reception and forwarding to aisstream.io whenever the boat has internet.
- House + starter battery voltage visible at home whenever the onboard router has power.
- Bilge water alarm (binary) with push notification to Pete and Kelly.
- Shore / generator / battery power source indication.
- Core temperature zones: cabin, engine compartment, refrigerator.
- Kelly-friendly "How's My Boat" dashboard card in HA.
- 12+ hour UPS runtime with shore power and house bank both dead.
- Zero-touch boot/recovery after any power cycle.
- OTA updates from home via VPN tunnel to the onboard router.

### Stretch Goals (later phases)
- Victron SmartShunt BLE telemetry (SoC, current, time remaining).
- GPS position + AIS-redundant location.
- Anchor drag and "broke free of slip" detection (geofence-based).
- Continuous bilge water level (ultrasonic) in addition to float switch.
- Tank level monitoring via existing senders.
- Full 10-zone temperature monitoring.
- Full boat dashboard (for Pete, separate from Kelly's minimal card).
- Redundant OCI + home relay for AIS (active/active).
- Redundant cloud + home MQTT brokers (bridged).

### Future v2 Ideas (not designed for)
- Remote actuation (bilge blower, cabin fan, heater).
- NMEA 2000 bridge.
- Engine RPM via alternator W terminal.
- Wind / barometric instruments.
- Companion "safety" ESP32 as independent watchdog.

### Explicit Non-Goals
- Replacing onboard chartplotters or displays.
- Providing data to onboard navigation instruments.
- Real-time collision avoidance (dAISy explicitly not rated for this).
- On-boat SignalK / OpenCPN server (already covered by existing hardware).

---

## 3. Requirements

### Functional
- **F-1** Receive AIS on channels 87B (161.975 MHz) and 88B (162.025 MHz), decode to NMEA AIVDM.
- **F-2** Expose raw AIS stream on local TCP port for local consumption (chartplotter, OpenCPN, etc.).
- **F-3** Forward AIS to aisstream.io via cloud relay when internet is available.
- **F-4** Monitor at least 3 temperature zones at v1, expandable to 10.
- **F-5** Monitor house bank and starter battery voltages.
- **F-6** Detect power source: shore (AC), generator (AC), and battery-only operation.
- **F-7** Binary bilge water detection via float switch.
- **F-8** Publish all telemetry to MQTT broker over TLS.
- **F-9** Support multiple stored WiFi SSIDs with RSSI-based selection.
- **F-10** Publish heartbeat every 60 s; HA detects ESP32 silent ≥ 5 min.
- **F-11** OTA firmware updates over local network (via VPN from home).
- **F-12** Auto-reboot on prolonged MQTT disconnect (10 failed reconnects).
- **F-13** Fallback WiFi AP mode if no known SSID is reachable after 5 minutes.

### Non-Functional
- **NF-1** Ambient operating temp −10 °C to +60 °C.
- **NF-2** 12 V DC input, 11.0–14.8 V tolerance, reverse-polarity protected.
- **NF-3** UPS 12+ hour runtime at typical load after primary power fails.
- **NF-4** Outage on power-source transition ≤ 5 minutes.
- **NF-5** All external cable entries strain-relieved at the enclosure.
- **NF-6** All parts commercial, from common distributors (Digi-Key, Mouser, Amazon, Adafruit, SparkFun).
- **NF-7** v1 BOM under ~$600 (excluding LTE router and Victron gear).
- **NF-8** Configuration fully documented and reproducible in the sailboat project.

---

## 4. Prior Art (drawn from)

| Source | What we're using |
|---|---|
| [open-boat-projects.org](https://open-boat-projects.org/en/) | NMEA patterns, alternator-W tach circuit (future), tank sender pattern |
| [Bareboat Necessities](https://bareboat-necessities.github.io/) | XDR sensor patterns, sensor catalogue |
| [Practical Boat Owner smart engine monitor](https://www.pbo.co.uk/expert-advice/how-i-installed-a-smart-engine-monitoring-system-on-my-sailboat-97830) | Single-ESP32 reference design with INA-style monitors |
| [Fabian-Schmidt/esphome-victron_ble](https://github.com/Fabian-Schmidt/esphome-victron_ble) | Victron BLE advertisement ingestion |
| [tube0013/esphome-stream-server-v2](https://github.com/tube0013/esphome-stream-server-v2) | UART→TCP bridge for AIS |
| [NauticApp/BilgeMonitor](https://github.com/NauticApp/BilgeMonitor) | Ultrasonic bilge level (stretch phase) |
| [Wegmatt dAISy HAT manual](http://www.wegmatt.com/files/dAISy%20HAT%20AIS%20Receiver%20Manual.pdf) | Serial breakout pattern (used without Raspberry Pi) |
| [aisstream.io](https://aisstream.io/documentation) | Contributor feed target |
| [L-36 DIY ESP32](https://l-36.com/DIY-ESP32) | Quiescent-current power design notes |

---

## 5. Logical Architecture

```
[Hunter 41DS]
   │
   ├── [AIS Transponder — Class B SOTDMA] ── VHF ── (airwaves)
   │
   ├── [Onboard 4×4 MIMO X75 LTE router]  ◄── WiFi ──┐
   ├── [Marina WiFi (when joinable)]      ◄── WiFi ──┤
   │                                                  ▼
   │   ┌──────────────────────────────────────────────────┐
   │   │  ESP32-S3 node ("BoatMon-1")                     │
   │   │                                                  │
   │   │  ┌──────────────┐  UART0 @ 38400                 │
   │   │  │ dAISy HAT    │─────────────►┐                 │
   │   │  │ (AIS RX)     │              │                 │
   │   │  └──────────────┘              ▼                 │
   │   │                         ┌──────────────┐         │
   │   │  [Sensors, I2C/1-wire]──►│  ESPHome    │         │
   │   │                         │  firmware    │         │
   │   │  [GPS UART2 — Phase 8]──►│             │         │
   │   │                         └──────┬───────┘         │
   │   │                                │                 │
   │   │  stream_server: TCP :6638 ◄────┤ (AIS raw)       │
   │   │  MQTT over TLS (all other) ◄───┘                 │
   │   └──────────────┬───────────────────┬───────────────┘
   │                  │                   │
   │                  │ AIS TCP           │ MQTT/TLS
   │                  │ (WireGuard to     │ (direct to
   │                  │  OCI relay)       │  cloud broker)
   │                  │                   │
   ▼──────────────────┴───────────────────┴─────────►  internet

   ┌──────────────────────────────────────────────────┐
   │ Oracle Cloud — Always Free Tier (ARM A1.Flex)    │
   │  ┌────────────────────┐   ┌────────────────────┐ │
   │  │ AIS relay (Python) │   │ Mosquitto MQTT     │ │
   │  │ • pulls TCP :6638  │   │ broker w/ TLS      │ │
   │  │ • pushes to        │   │ (Let's Encrypt)    │ │
   │  │   aisstream.io     │   │                    │ │
   │  │ • WireGuard peer   │   │                    │ │
   │  └─────────┬──────────┘   └─────────┬──────────┘ │
   └────────────┼────────────────────────┼────────────┘
                │                        │
                ▼                        │
        [aisstream.io]                   │
                                         │
                                         ▼
                         ┌──────────────────────────┐
                         │ Home Assistant (home)    │
                         │ • MQTT subscriber        │
                         │ • Recorder (long-term)   │
                         │ • Automations / alerts   │
                         │ • Kelly's tablet (PWA):  │
                         │   "How's My Boat" card   │
                         └──────────────────────────┘
```

### Data flow summary

1. **AIS path:** dAISy → ESP32 UART → `stream_server` TCP :6638 → OCI relay (over WireGuard) → aisstream.io contributor feed → any subscriber (Pete's future app, VesselFinder, MarineTraffic subscribers, etc.).
2. **Telemetry path:** Sensors → ESP32 → MQTT publish (TLS) → OCI Mosquitto → HA subscribes → recorder + automations.
3. **Kelly's view:** HA Lovelace card served as PWA on home tablet; always-on Fully Kiosk Browser.
4. **OTA path:** Pete's laptop → WireGuard to home → WireGuard to onboard LTE router → LAN to ESP32 → ESPHome OTA.

---

## 6. Networking Design

### WiFi priority
Multiple SSIDs stored. ESPHome picks strongest available at connect time.

```yaml
wifi:
  networks:
    - ssid: BoatNet5G        # onboard LTE router (primary)
      priority: 100
    - ssid: SafeHarborGuest  # marina WiFi (if PSK, not captive portal)
      priority: 50
    - ssid: PeteHome         # when boat is trailered home (edge case)
      priority: 25
  reboot_timeout: 0s         # do NOT reboot on WiFi loss — local AIS TCP must keep serving
  ap:
    ssid: BoatMon-Fallback
    password: !secret ap_fallback_pw
```

### Connectivity modes
- **Underway:** onboard router powered, cellular backhaul, full telemetry + AIS.
- **At slip with shore power, router on:** same as underway.
- **At slip, router off:** ESP32 offline. Telemetry gap; MQTT `last-will` declares "offline." AIS TCP still serves any local client on boat LAN (none expected). Critical: explicitly not a design requirement to cover this window.
- **Recovery:** after any outage, ESP32 reconnects WiFi → reconnects MQTT → HA entities repopulate from retained messages.

### Captive portals
Not solvable in stock ESPHome. v1 approach: ignore marina WiFi; rely on onboard router. If a marina offers true PSK-auth WiFi, add to network list.

### Outbound DNS
Set to 1.1.1.1 in config; don't rely on DHCP-provided DNS (mitigates marina tampering).

### Remote admin
- WireGuard: Pete's home → OCI → boat router → ESP32 (OTA, debug).
- SSH into OCI VMs from anywhere.
- MQTT is public internet with TLS; no VPN needed for normal data flow.

---

## 7. AIS Data Path

### Onboard
- dAISy HAT serial breakout (not the Pi GPIO header) — three wires: 3.3V, GND, TX → ESP32 UART RX.
- ESPHome `uart` at 38400 baud, RX buffer 4 KB.
- `stream_server` (tube0013 fork, actively maintained) exposes raw NMEA AIVDM on TCP :6638.

### Local consumers (onboard LAN)
- Any NMEA-over-TCP client can connect to :6638 (chartplotters, OpenCPN, etc.).
- Zero code on ESP32 beyond the stream_server component.

### Cloud relay
- Small Python service on OCI ARM A1.Flex VM.
- Maintains persistent TCP client to ESP32 :6638 **via WireGuard** (boat initiates tunnel to OCI; sidesteps LTE NAT entirely).
- Forwards per-line AIVDM to aisstream.io contributor endpoint.
- Reconnect/retry logic; metrics to stdout; logs archived to OCI object storage (still within free tier).

### Why a relay and not direct-from-ESP32
| Reason | Detail |
|---|---|
| Reliability | Persistent TCP with clean reconnect on server, vs transient WiFi on MCU. |
| Buffering | Relay holds messages during aisstream outages; ESP32 RAM cannot. |
| Key hygiene | API key on server, not in firmware flash; rotation without reflash. |
| API drift | Protocol changes absorbed by redeploying a script, not a firmware update at sea. |
| Observability | Easier to monitor from cloud logs than from a boat MCU. |

### HA option (stretch): second relay at home
- Home relay pulls same TCP stream, pushes to aisstream in parallel.
- aisstream dedupes on MMSI+timestamp.
- Loses if: OCI relay down AND home internet down simultaneously (rare).
- Negligible cost; enable once v1 is stable.

---

## 8. Telemetry Path

### Broker
- Eclipse Mosquitto on OCI ARM A1.Flex.
- TLS via Let's Encrypt (DNS-01 challenge against Pete's existing domain, sub-domain e.g. `mqtt.peteskrake.com` or similar).
- Username/password auth per device; ACLs restricting each device to its own topic tree.

### Topic hierarchy
```
boat/hunter41/status/online                  (retained, LWT)
boat/hunter41/power/shore                    (0/1)
boat/hunter41/power/generator                (0/1)
boat/hunter41/power/source                   ("shore"|"generator"|"battery")
boat/hunter41/power/battery/house/v          (float V)
boat/hunter41/power/battery/start/v          (float V)
boat/hunter41/power/battery/house/soc        (0..100, Phase 7 via Victron BLE)
boat/hunter41/power/battery/house/current    (float A, Phase 7)
boat/hunter41/temp/cabin                     (float °C)
boat/hunter41/temp/engine_compartment        (float °C)
boat/hunter41/temp/refrigerator              (float °C)
boat/hunter41/temp/<zone>                    (expandable to 10)
boat/hunter41/bilge/water_detected           (0/1)
boat/hunter41/tank/fresh_water/pct           (Phase 8)
boat/hunter41/tank/holding/pct               (Phase 8)
boat/hunter41/tank/fuel/pct                  (Phase 8)
boat/hunter41/location/lat                   (Phase 8)
boat/hunter41/location/lon                   (Phase 8)
boat/hunter41/location/sog                   (Phase 8)
boat/hunter41/location/cog                   (Phase 8)
boat/hunter41/health/rssi
boat/hunter41/health/uptime_s
boat/hunter41/health/free_heap
boat/hunter41/health/ip
```

### HA subscriber
- HA MQTT integration → OCI broker over TLS (stock integration, no customization).
- ESPHome's MQTT discovery (`discovery_prefix: homeassistant`) auto-creates entities.
- All entities grouped under one device: "Hunter 41DS — BoatMon".

### Long-term storage
- HA recorder (default SQLite) for ~10 days of 1-minute data.
- InfluxDB add-on (optional, Phase 10) for multi-year retention with graphing.

### High-availability option (stretch)
- Mosquitto bridge at home subscribing to OCI broker.
- HA reads from local bridge.
- If OCI down: HA sees last retained values.
- If home internet down: OCI continues collecting.
- Bridge is ~3 lines of config; enable once v1 is stable.

---

## 9. Hardware Bill of Materials

### Core compute & I/O

| Item | Part | Qty | Source | Est. $ |
|---|---|---|---|---|
| ESP32 module | ESP32-S3-DevKitC-1-N16R8V (16 MB flash / 8 MB PSRAM) | 1 | Digi-Key / Mouser / Adafruit | 15 |
| Screw-terminal breakout | CZH-Labs ESP32-DevKitC screw terminal shield, 5 mm pitch, OR DIYables 38-pin ESP32 screw adapter | 1 | czh-labs.com / Amazon | 20 |
| AIS receiver | Wegmatt dAISy HAT (used via breakout pads, not Pi header) | 1 | shop.wegmatt.com | 75 |

### Enclosure & mounting

| Item | Part | Qty | Source | Est. $ |
|---|---|---|---|---|
| Main enclosure | Polycase WC-23F (IP66 ABS, 6.3×4.3×3.5") OR Bud NBB-15242 | 1 | polycase.com / buddibud | 35 |
| DIN rail (internal) | TS-35 aluminum, 6" | 1 | Digi-Key | 5 |
| Cable glands | M12 and M16 PG nylon | 6 | Amazon | 10 |
| Strain reliefs | Heyco SR bushings, assorted | 4 | Digi-Key | 5 |

### External connectors (bulkhead)

| Item | Part | Qty | Source | Est. $ |
|---|---|---|---|---|
| M12 A-coded 5-pin panel-mount (female) | TE Connectivity T4171220005-001 or Amphenol equivalent | 4 | Digi-Key | 15 ea |
| M12 cable-mount plug (male, mate) | TE Connectivity matching mate | 4 | Digi-Key | 8 ea |

### Power subsystem

| Item | Part | Qty | Source | Est. $ |
|---|---|---|---|---|
| 12V→USB-C PD buck converter | Drok or VCELEDINS 12V→USB-C PD 20V/5V, ≥45 W, high-quality | 1 | Amazon | 25 |
| ATO fuse holder | Blue Sea 5005 + 5A fuse | 1 | Defender / West Marine | 10 |
| TVS diode | SMCJ30A (30V unidirectional) | 1 | Digi-Key | 1 |
| Bulk input capacitance | 1000 µF 25V low-ESR electrolytic | 1 | Digi-Key | 2 |
| USB-C power bank (pass-through) | Voltaic V50 (12.8 Ah / 47 Wh, explicit pass-through) OR INIU P63-E1 (verify pass-through before committing) | 1 | voltaicsystems.com / Amazon | 60 |
| USB-C cables, short, quality | 2 | Anker / Amazon | 10 |

### Sensors (Phase 5 / v1)

| Item | Part | Qty | Source | Est. $ |
|---|---|---|---|---|
| Temperature — waterproof 1-wire | DS18B20 waterproof, 1 m lead | 3 (expandable) | Adafruit / Amazon | 8 ea |
| 1-wire pullup | 4.7 kΩ resistor | 1 | — | 0.1 |
| House battery V / A sense | INA226 breakout (I²C) + appropriate shunt | 1 | Adafruit / Amazon | 12 |
| Starter battery V sense | Voltage divider: 100 kΩ + 33 kΩ, 1% metal film | 1 | — | 1 |
| Shore power detect | HiLetgo 120 V AC opto-isolator module | 1 | Amazon | 8 |
| Generator power detect | Second 120 V opto-isolator OR ACS712 on genset output leg | 1 | Amazon | 8 |
| Bilge float switch | Rule-A-Matic Plus 35A or Johnson Ultima | 1 | Defender | 25 |

### Sensors (Phases 7–10)

| Item | Part | Qty | Source | Est. $ |
|---|---|---|---|---|
| Victron SmartShunt 500A | (if not installed as part of electrical upgrade) | 1 | Defender | 170 |
| GPS module | u-blox NEO-M9N on SparkFun GPS-15210 breakout | 1 | SparkFun / Digi-Key | 50 |
| GPS active antenna | 28 dB active, SMA, with ground plane | 1 | Digi-Key | 15 |
| ADC for tank senders | Adafruit ADS1115 16-bit 4-channel I²C | 1 | Adafruit | 15 |
| Additional DS18B20 sensors | | 7 | Adafruit / Amazon | 56 |
| Ultrasonic bilge level (stretch) | JSN-SR04T-V3.0 waterproof ultrasonic | 1 | Amazon | 10 |

### Wire & consumables

| Item | Spec | Qty |
|---|---|---|
| Power wire (red + black) | 16 AWG tinned marine (Ancor) | 10 ft ea |
| Signal wire | 22 AWG tinned stranded, marine grade, assorted colors | 50 ft |
| Ferrules | Uninsulated, 20–22 AWG | 100 pcs |
| Ferrule crimp tool | Knipex 97 53 14 or similar | 1 |
| Heat shrink | Marine-grade adhesive-lined, assorted | Kit |

### Cloud infrastructure

| Item | Cost |
|---|---|
| Oracle Cloud Always Free: 2× ARM A1.Flex VMs (4 OCPU / 24 GB RAM total) | $0 forever |
| Domain + Let's Encrypt TLS | $0 (sub-domain of existing) |
| Mosquitto, WireGuard, Python | $0 (open source) |

### Estimated totals

| Phase group | Approx cost |
|---|---|
| Phases 1–4 (bench + core + install) | $325 |
| Phase 5 (core sensors) | $80 |
| Phase 6 (alerts — software only) | $0 |
| Phase 7 (Victron BLE; SmartShunt already installed assumed) | $0 |
| Phase 8 (GPS + tanks) | $80 |
| Phase 9 (anchor drag) | $0 |
| Phase 10 (expanded temp + full dashboard) | $60 |
| Phase 11+ (stretch: continuous bilge, redundancy) | $15+ |
| **v1 functional (Phases 1–6)** | **~$405** |
| **Full Phase 1–10 build** | **~$545** (assuming SmartShunt already installed) |

---

## 10. Power Subsystem Design

### Input chain

```
12V house bank
  │
  ├── ATO 5A fuse (at the source, per ABYC)
  │
  ├── Reverse polarity (P-MOSFET or Schottky)
  │
  ├── TVS diode SMCJ30A
  │
  ├── 1000 µF low-ESR bulk cap
  │
  ▼
12V → USB-C PD buck converter (>45W)
  │
  ▼
USB-C "pass-through" power bank
  │
  ▼
USB-C → ESP32-S3-DevKitC USB-C port
```

### UPS logic
- Pass-through power bank: when 12V is present, it charges the internal cell while delivering power; when 12V drops, the cell takes over seamlessly.
- **Hard requirement:** bank must explicitly support simultaneous charge + discharge (true pass-through). Many "pass-through" claims are misleading — bench-verify before final install.
- Load: ESP32 + dAISy + GPS + sensors ≈ 1.5–2 W at 12 V input.
- 47 Wh power bank → 20–30+ hours runtime. Exceeds 12-hour requirement by 2×.

### Brownout handling
- ESP32-S3 hardware brownout detector configured via ESPHome.
- Bulk capacitance rides through engine-start dips (typical 2–3V, 100–500 ms).
- No SD card to corrupt; ESPHome config in flash.

### Quiescent considerations
- Not a primary concern given house bank is ≥300 Ah and this system draws ~4 Ah/day.
- UPS power bank self-discharge ~3–5%/month (Li-ion) is the larger concern for stored-boat scenarios; periodic charge from house bank trickle solves it.

---

## 11. Firmware Architecture

### Framework
- **ESPHome** (YAML-driven).
- External components:
  - `github://tube0013/esphome-stream-server-v2` — AIS TCP bridge.
  - `github://Fabian-Schmidt/esphome-victron_ble` — Victron BLE (Phase 7).

### File layout
```
boat-mon/
  boat-mon.yaml              # main device config
  secrets.yaml               # (gitignored) WiFi, MQTT, OTA creds
  packages/
    base.yaml                # logger, api, ota, wifi, fallback AP
    network.yaml             # MQTT client + LWT
    ais.yaml                 # uart + stream_server
    temperature.yaml         # 1-wire bus + per-zone sensors
    power.yaml               # INA226, voltage divider, opto-isolators
    bilge.yaml               # float switch binary sensor
    health.yaml              # RSSI, uptime, free heap, IP
    victron.yaml             # (Phase 7) BLE advertisement components
    gps.yaml                 # (Phase 8) uart2 + GPS component
    tanks.yaml               # (Phase 8) ADS1115 + calibration tables
```

### Watchdog / resilience
- Hardware WDT enabled.
- Heartbeat publish every 60 s (`health/uptime_s`). HA detects silent >5 min, pushes alert.
- Reboot after 10 failed MQTT reconnects.
- AP fallback after 5 min of no known SSID.

### OTA policy
- Only reachable from onboard LAN (gated at router).
- Pete reaches via WireGuard tunnel.
- Password protected, encrypted.

---

## 12. Home Assistant Integration

### Configuration (zero custom code)
- Stock MQTT integration → `mqtts://mqtt.peteskrake.com:8883` (or similar).
- ESPHome MQTT discovery auto-creates all entities under device "Hunter 41DS — BoatMon".

### Entities (Phase 5 deliverable)
- `binary_sensor.boatmon_online`
- `binary_sensor.boatmon_bilge_water`
- `binary_sensor.boatmon_shore_power`
- `binary_sensor.boatmon_generator`
- `sensor.boatmon_house_battery_v`
- `sensor.boatmon_starter_battery_v`
- `sensor.boatmon_cabin_temp`
- `sensor.boatmon_engine_temp`
- `sensor.boatmon_fridge_temp`
- `sensor.boatmon_rssi`
- `sensor.boatmon_uptime`

### Kelly's "How's My Boat" card

Rough Lovelace layout (glance-style + conditional):

- **Top row:** boat icon + "Boat is ONLINE / OFFLINE" (based on last-seen <5 min).
- **Row 2:** Power source: icon (shore plug / generator / battery) + color (green shore, yellow genset, red battery-only at slip).
- **Row 3:** House battery V (traffic light: green ≥12.4, yellow 12.0–12.4, red <12.0) + "Low!" badge if alert fired.
- **Row 4:** Bilge: big green "Dry" or big red "WATER DETECTED."
- **Row 5:** Three temperature tiles (cabin / engine / fridge), each green/red based on configured ranges.
- **Tap target at bottom:** "Details →" → Pete's full dashboard (Phase 10).

Served via Fully Kiosk Browser on a wall-mounted 10" Android tablet in the kitchen. PWA/dashboard auto-refreshes.

### Automations

| Trigger | Action | Phase |
|---|---|---|
| `bilge_water_detected` rises | Push (Pete + Kelly), TTS on home speakers, email | 6 |
| `house_battery_v` < 11.8 for 5 min | Push + email | 6 |
| `boatmon_online` → false for 15 min | Push to Pete only (avoid alarming Kelly for mundane WiFi hiccups) | 6 |
| `shore_power` falls while docked + home WX shows storm | Push to Pete | 6 |
| GPS position > 50 m from armed anchor point | Push critical (Pete + Kelly) | 9 |
| `generator` rises | Log event, notify Pete (informational) | 6 |

---

## 13. Build Phases

Each phase produces **working end-to-end functionality**; Pete can stop at any phase and have a useful system.

### Phase 1 — Bench prototype (AIS → local TCP)
**Goal:** Prove AIS reception, learn tooling.
**Hardware:** M5Atom (existing) OR ESP32-S3-DevKitC-1, dAISy HAT wired via 3 jumpers, desktop VHF whip.
**Software:** Minimal ESPHome YAML: `uart` + `stream_server`. WiFi to home network.
**Verify:** `telnet <esp32-ip> 6638` shows live AIS NMEA. Load in OpenCPN as TCP input.
**Exit criteria:** AIS streaming on Pete's desk.
**Time:** 1–2 evenings.

### Phase 2 — Cloud infrastructure (broker + AIS relay)
**Goal:** Stand up OCI side before touching the boat.
**Work:**
- Sign up OCI; provision 2× ARM A1.Flex VMs.
- Install + configure Mosquitto with TLS (Let's Encrypt DNS-01).
- Write Python AIS relay (or adapt existing open-source).
- Install WireGuard on OCI; establish tunnel to Pete's home for testing.
- Point HA at cloud broker.
**Verify:** MQTT round-trip from bench ESP32 to HA. Pete's MMSI (or a test MMSI) visible on aisstream.
**Exit criteria:** Cloud pipeline proven with bench prototype.
**Time:** One weekend.

### Phase 3 — Hardened core platform
**Goal:** Build the actual boat-ready unit.
**Work:**
- Final ESP32-S3 + breakout + dAISy in Polycase enclosure.
- 12V→USB-C buck, pass-through power bank, fuse, TVS.
- M12 bulkhead connectors installed; wiring dressed; ferrules on all stranded.
- OTA password set; WireGuard test from laptop.
**Verify:** 72-hour bench soak. Simulate power cuts with 12V dummy load bench. Confirm OTA works.
**Exit criteria:** Unit ready for boat.
**Time:** Full weekend.

### Phase 4 — Boat install + connectivity
**Goal:** Mount on boat, establish operating connectivity.
**Work:**
- Install in nav station or dry locker.
- 12V feed from house bank with fuse at source.
- AIS antenna (splitter off existing VHF vs dedicated — decide at install time per mast/rigging inspection).
- ESP32 joins onboard LTE router.
**Verify:** AIS visible on aisstream from slip. MQTT heartbeats in HA. Kelly's card shows boat online.
**Exit criteria:** Unit reporting from the marina.
**Time:** 1 day install + commissioning.

### Phase 5 — Core sensors
**Goal:** Meaningful boat health in HA.
**Hardware added:** 3× DS18B20 (cabin / engine / fridge), INA226 (house bank), divider (starter), 2× opto-isolators (shore + genset).
**Verify:** All values reasonable; historical graphs tracking correctly.
**Exit criteria:** Kelly's "How's My Boat" card fully populated.
**Time:** 1 day.

### Phase 6 — Critical alerts
**Goal:** Safety coverage via HA automations.
**Hardware:** Float switch in bilge → GPIO.
**Software:** HA automations per table in §12; tune thresholds after a week of data.
**Verify:** Manually trigger each alert; confirm delivery (push, TTS, email). 14-day soak with no false positives.
**Exit criteria:** All alerts proven.
**Time:** Half day + tuning.

### Phase 7 — Victron BLE telemetry
**Goal:** High-resolution battery data without new wiring.
**Prerequisite:** SmartShunt installed (part of electrical upgrade plan).
**Hardware:** None (ESP32-S3 has BLE built in).
**Software:** Add `victron_ble` external component; pair via MAC + bindkey.
**Verify:** All SmartShunt values match Victron app; HA history matches reality over a charge/discharge cycle.
**Exit criteria:** Battery SoC, current, time-to-go, temperature in HA.
**Time:** 2–3 hours.

### Phase 8 — GPS + tank levels
**Goal:** Position + fluid inventory.
**Hardware:** u-blox NEO-M9N on UART2, active antenna at cabin top; ADS1115 ADC tapped off tank senders.
**Software:** Native ESPHome `gps` component; ADC with per-tank calibration lookup.
**Verify:** GPS position within 5 m; tanks match dipstick.
**Exit criteria:** Position + tanks in HA and MQTT.
**Time:** One weekend (tank calibration is the time sink).

### Phase 9 — Anchor drag + slip breakaway
**Goal:** Location-aware safety.
**Hardware:** None (GPS from Phase 8).
**Software:** HA automations:
- **Slip mode (always armed):** geofence around Safe Harbor Sandusky slip. Alert on leave.
- **Anchor mode (manual arm):** alert if position >50 m from armed point OR speed >0.5 kt sustained 2 min.
**Verify:** 14-day soak at slip with no false positives. Manually simulate breakaway by moving armed point in HA.
**Time:** Half day.

### Phase 10 — Full telemetry + full dashboard
**Goal:** Complete boat telemetry; Pete's full dashboard.
**Hardware:** 7 more DS18B20 on same 1-wire bus (star topology with pullup near ESP32; split to a second bus if needed).
**Software:** Full HA dashboard with graphs, trend cards, InfluxDB optional.
**Exit criteria:** Pete has full visibility; Kelly retains her simpler card.
**Time:** One weekend.

### Phase 11+ (future / stretch)
- Continuous bilge level (JSN-SR04T ultrasonic).
- Remote actuation (bilge blower, cabin fan, heater relay).
- Engine RPM via alternator W terminal (optocoupler + frequency counter).
- Wind / barometric instruments.
- NMEA 2000 bridge (separate CAN board).
- Second safety-only ESP32 as independent watchdog.
- Redundant AIS relay: OCI + home active/active.
- Redundant MQTT brokers: cloud + home bridged.

---

## 14. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Single ESP32 crash silences alarms | Med | High | HA heartbeat timeout alert; consider safety ESP32 in v2 |
| Pass-through power bank doesn't actually pass-through | Med | Med | Bench-verify before final install; have a second unit on hand |
| Marina WiFi captive portal unusable | High | Low | Rely on onboard LTE router; revisit if a marina offers PSK |
| aisstream.io API change | Med | Low | Relay absorbs; redeploy Python script |
| OCI free tier policy change | Low | Med | Stateless services; migrate to alternative (Fly.io, Hetzner) in hours |
| 1-wire bus flaky on long runs | Med | Low | Shielded cable; pullup near ESP32; split buses if >5 m total |
| Engine-start transient damages ESP32 | Low | High | TVS + bulk cap + fuse; no direct 12V to ESP32 |
| ESP32 overheats in summer | Med | Med | Dry locker install, not sealed outdoor box; internal temp sensor flags issue |
| WiFi drops persistently — no remote recovery | Low | Med | AP fallback after 5 min; Pete reboots at next boat visit |
| Onboard router off when boat is at slip | Med | Low | Accepted design limitation; HA marks offline |

---

## 15. Open Questions (resolve in sailboat project)

1. **Does the purchased Hunter 41DS have an AIS transponder?** If not, budget Class B+ SOTDMA (Vesper Cortex V1 or em-trak B954, ~$900–1,500).
2. **AIS antenna strategy:** splitter vs dedicated — decide at install after mast/rigging inspection.
3. **Victron SmartShunt** timing vs. Phase 7.
4. **Onboard LTE router admin setup:** WireGuard server config documented in sailboat project.
5. **Home WireGuard setup** to OCI VM for OTA path.
6. **Tank sender resistance standard** on Hunter 41DS (likely US 240–33Ω, verify).
7. **Marina WiFi auth** at Safe Harbor Sandusky — PSK or captive portal? Test on first slip visit.
8. **MQTT device naming convention:** settle before deployment (`boat/<mmsi>/...` vs `boat/hunter41/...` etc.).
9. **Dedicated MQTT TLS cert sub-domain** vs sub of existing.
10. **Pass-through power bank final selection** after bench test.

---

## 16. Appendix A — Starter ESPHome YAML (Phase 1)

```yaml
esphome:
  name: boatmon-1
  friendly_name: "Hunter 41DS BoatMon"

esp32:
  board: esp32-s3-devkitc-1
  framework:
    type: esp-idf

external_components:
  - source: github://tube0013/esphome-stream-server-v2

logger:
  level: INFO

api:
  encryption:
    key: !secret api_key

ota:
  platform: esphome
  password: !secret ota_password

wifi:
  networks:
    - ssid: !secret boat_wifi_ssid
      password: !secret boat_wifi_password
      priority: 100
  reboot_timeout: 0s
  ap:
    ssid: "BoatMon-Fallback"
    password: !secret ap_fallback_password

captive_portal:

uart:
  id: daisy_uart
  rx_pin: GPIO18
  tx_pin: GPIO17
  baud_rate: 38400
  rx_buffer_size: 4096

stream_server:
  uart_id: daisy_uart
  port: 6638

mqtt:
  broker: !secret mqtt_broker
  port: 8883
  username: !secret mqtt_user
  password: !secret mqtt_pass
  discovery: true
  discovery_prefix: homeassistant
  ssl_fingerprints:
    - !secret mqtt_fingerprint
  birth_message:
    topic: boat/hunter41/status/online
    payload: "ON"
    retain: true
  will_message:
    topic: boat/hunter41/status/online
    payload: "OFF"
    retain: true

sensor:
  - platform: wifi_signal
    name: "BoatMon RSSI"
    update_interval: 60s
  - platform: uptime
    name: "BoatMon Uptime"
    update_interval: 60s

binary_sensor:
  - platform: stream_server
    stream_server: !extend
    name: "BoatMon AIS TCP client connected"
```

---

## 17. Appendix B — Sensor pinout plan (ESP32-S3-DevKitC-1)

| Pin | Use | Notes |
|---|---|---|
| GPIO17 | UART1 TX → dAISy RX (unused, TX not needed) | — |
| GPIO18 | UART1 RX ← dAISy TX | AIS data in |
| GPIO4 | 1-Wire DS18B20 bus | 4.7 kΩ pullup to 3.3V |
| GPIO8 | I²C SDA | INA226, ADS1115, etc. |
| GPIO9 | I²C SCL | — |
| GPIO5 | Bilge float switch | Internal pullup; switch to GND |
| GPIO6 | Shore power opto-isolator | Internal pullup |
| GPIO7 | Generator power opto-isolator | Internal pullup |
| GPIO1 (ADC1_CH0) | Starter battery voltage divider | — |
| GPIO15 | UART2 RX ← GPS | Phase 8 |
| GPIO16 | UART2 TX → GPS | Phase 8 |

---

*End of document v1.0.*
