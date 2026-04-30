# EvenKeel — Existing Sensor & NMEA 2000 / 0183 Integration

**Question:** Can EvenKeel read from sensors and instruments that already exist on the boat — including the NMEA 2000 backbone if one is installed?
**Answer:** Yes, through a "Tap, don't replace" architecture that adds a sixth tier to the [sensor expansion model](sensor-expansion.md). Three integration paths: dedicated CAN-ESP32 (DIY), commercial N2K gateway + SignalK on the boat Pi (turn-key), or NMEA 0183 over UART (legacy boats and older talkers).

---

## 1. The "Tap, Don't Replace" Principle

The original design (`research/sailboat-monitor-design.md §2`) listed as **explicit non-goals**:
- "Replacing onboard chartplotters or displays."
- "Providing data to onboard navigation instruments."
- "On-boat SignalK / OpenCPN server (already covered by existing hardware)."

These remain non-goals. EvenKeel does not write to N2K, does not pretend to be a chartplotter, does not run primary navigation.

**What changes:** EvenKeel becomes a **read-only listener** on whatever marine bus already exists, ingesting data into the same MQTT topic tree HA already consumes. This is additive — the chartplotter, autopilot, and instruments keep doing their jobs. EvenKeel just gets a richer dataset for free.

Updated non-goal phrasing for `architecture.md`:
- ✅ Listening to N2K / 0183 traffic for telemetry → **allowed** (read-only)
- ❌ Sending to N2K / 0183 → still **not in scope**
- ❌ Replacing chartplotter → still **not in scope**
- ❌ Real-time collision avoidance / nav-grade routing → still **not in scope**

---

## 2. What's Likely on the Hunter 41DS

The Hunter 41DS came in multiple production years (2008–2014). Equipment varies, but typical:

| Equipment | Bus | Likelihood | What it'd give EvenKeel |
|---|---|---|---|
| Chartplotter (Raymarine c70/e95, Garmin 5212, B&G Zeus) | N2K | High | GPS lat/lon, COG, SOG, route, waypoints |
| Wind transducer (B&G H5000, Raymarine i70) | N2K | Medium | apparent/true wind speed + angle |
| Depth sounder (Airmar B60/P79) | N2K | High | depth below transducer |
| Speed (paddle wheel or pitot) | N2K | Medium | speed-through-water |
| Autopilot (Raymarine SmartPilot, B&G H5) | N2K | Medium | heading, rudder angle |
| Engine — older Yanmar 4JH3/4JH4/4JH5 | mostly NONE | High | nothing without retrofit |
| Engine — newer Yanmar with VC10 / SmartCraft | J1939 → N2K bridge | Low (newer boats) | RPM, fuel rate, hours, temp |
| Battery monitor (Mastervolt, Victron BMV) | N2K (some) / VE.Direct | Medium | SoC, V, I, time-to-go |
| AIS transponder (Vesper, em-trak) | N2K + 0183 | Medium | already-installed transponder |
| VHF DSC | 0183 (older) / N2K (newer) | High | distress events, GPS |

**Bottom line:** if the Hunter has *any* MFD/chartplotter newer than ~2012, there's almost certainly an N2K backbone behind a backbone tee under the helm or in the nav station. EvenKeel can read it.

> **Resolve at survey:** open question Q40 below — confirm which buses exist before designing this phase. Until confirmed, treat N2K integration as a Phase 11+ opt-in, not in v1.

---

## 3. Three Integration Paths

### Path A — DIY: Dedicated CAN-ESP32 → MQTT

A second ESP32 board with a built-in CAN transceiver taps the N2K backbone via a standard tee + drop cable, decodes selected PGNs (Parameter Group Numbers), and republishes to MQTT.

**Hardware (~$60):**

| Item | Part | $ |
|---|---|---|
| **Waveshare ESP32-S3 CAN-FD** (or ESP32-S3-Touch-LCD-4.3 — has CAN onboard) | Waveshare | $25 |
| **Maretron MD-MD-4 micro tee** (or Raymarine/Garmin equivalent — depends on existing backbone connector type) | Maretron | $20 |
| **0.5m N2K drop cable**, micro-male to micro-female | Maretron / Garmin | $15 |

Total: **~$60** plus the second ESP32. If you choose the Touch-LCD-4.3 board, this satellite *also* becomes the optional Tier-1 LVGL panel from the Phase 11+ plan — one board, two purposes.

**Software:**
- ESPHome's `canbus:` component supports the ESP32-S3's built-in TWAI controller (CAN 2.0B). Confirmed working as of ESPHome 2024.6+.
- Decode N2K with one of:
  - **`ttlappalainen/NMEA2000` library** (de facto Arduino library) — call from ESPHome via `external_components` / custom C++. Most complete decoder.
  - **`AK-Homberger/NMEA2000-Workshop`** — collection of decoded examples.
  - **Hand-rolled lambdas** for just the PGNs you care about — fine if you only want 5–10 types.
- Republish to MQTT topics that match EvenKeel's convention.

**Sample ESPHome config sketch:**

```yaml
# firmware/satellites/n2k-bridge.yaml
esphome:
  name: n2k-bridge
  platformio_options:
    build_flags: -DUSE_N2K
  includes:
    - n2k_handler.h

external_components:
  - source: github://ttlappalainen/NMEA2000

canbus:
  - platform: esp32_can
    tx_pin: GPIO0
    rx_pin: GPIO1
    can_id: 0
    bit_rate: 250kbps    # N2K standard

# In n2k_handler.h, register listeners for PGNs of interest:
# 129025  Position rapid-update      (lat/lon at 10 Hz)
# 129026  COG/SOG rapid-update
# 130306  Wind data
# 128267  Water depth
# 127245  Rudder
# 127488  Engine parameters rapid (RPM)
# 127489  Engine parameters dynamic (fuel rate, oil temp, hours)
# 127508  Battery status
# 130316  Temperature extended

# On each PGN: decode, publish via mqtt::publish to e.g.
#    boat/hunter41/nav/lat
#    boat/hunter41/wind/apparent_speed
#    boat/hunter41/engine/rpm
#    boat/hunter41/depth/below_transducer
```

**Pros:**
- DIY, fits the project ethos, ~$60, no commercial gateways
- Full control over which PGNs get republished
- Reuses the existing MQTT bridge to home HA — no new pipe
- One firmware repo, one OTA story

**Cons:**
- Decoder code is a few hundred lines of C++ (hand-roll) or pulls in a sizable library
- No protocol "validation" beyond what ttlappalainen does — bugs could in theory misbehave on the bus (read-only, so bounded blast radius, but still)

**Risk mitigation: use a galvanic isolator drop**
- N2K backbone shares ground across all devices; an isolation tap protects against ground-loop currents (boats are sloshy electrochemical environments).
- **Yacht Devices YDIM-01** N2K isolator (~$80) sits in-line on a drop. Optional but recommended.

### Path B — Commercial: N2K gateway + SignalK on the boat Pi

Plug a USB-to-N2K gateway into the on-boat Raspberry Pi and run SignalK Server. SignalK ingests N2K, normalizes to a standard data model, and publishes to MQTT.

**Hardware:**

| Item | Part | $ |
|---|---|---|
| **Yacht Devices YDNU-02** USB N2K gateway | YDNU-02 | $150 |
| Or **Actisense NGT-1-USB** (more featureful) | NGT-1-USB | $220 |
| N2K tee + drop cable (same as Path A) | — | $35 |

Total: **$185–255**.

**Software (all free, all open source):**
- **SignalK Server** runs as a systemd service or HA add-on on the Pi. Mature, multi-protocol.
- **`@signalk/signalk-to-mqtt`** plugin publishes any SignalK path to MQTT topics. Configure once.
- **`@signalk/n2k-signalk`** is the N2K input plugin; talks to the YDNU-02/NGT-1 over `/dev/ttyUSB0`.
- Optional: **SignalK Kip** dashboard renders any value to a browser — bonus on-boat dashboard for free.

**Why SignalK is worth knowing:**
- It's an open standard (not a vendor product).
- It accepts N2K, NMEA 0183, ESPHome, Victron, Modbus, raw MQTT, and more — and unifies them under one data model. Anything you add later (Phase 11+ wind, autopilot, etc.) lands in the same tree.
- HA has a native [SignalK integration](https://github.com/SignalK-HA/home-assistant-signalk) via REST/WebSocket — entities auto-populate.

**Pros:**
- Turn-key. You point SignalK at the gateway and entities appear in HA.
- Battle-tested decoder; thousands of installations.
- Future-proof — add any other protocol later, SignalK swallows it.
- Free Kip dashboard as a bonus.

**Cons:**
- $185–255 in hardware vs $60 DIY.
- Adds another long-running service on the Pi to maintain.
- One more open-source project to track.

### Path C — Off-the-shelf wireless: N2K WiFi gateway

For users who don't want EvenKeel reading the bus at all but just want phone apps (iSailor, iNavX, NavionicsNautic) to see the data.

**Hardware:**

| Item | $ |
|---|---|
| Yacht Devices **YDWG-02** N2K Wi-Fi gateway | $230 |
| Vesper **WatchMate 850** (if no AIS yet) | $1,200 |

Doesn't help EvenKeel directly. Mention only because some boat owners install one for navigation use; if it's already there, EvenKeel can sometimes ingest its TCP/UDP NMEA-over-WiFi output, but that's a Path-D stretch case.

---

## 4. NMEA 0183 — for older boats / specific talkers

Some boats have no N2K, only the older **NMEA 0183** serial standard. EvenKeel already uses 0183 for AIS (dAISy → ESP32 UART → TCP). The same pattern reads any other 0183 talker:

- 4800 baud (38400 for AIS) RS-422 differential serial
- Each device has TX/RX pairs; multiple talkers need a multiplexer (Shipmodul MiniPlex, Actisense NMEA Multiplexer)
- Sentences look like `$GPRMC,...` (GPS), `$WIMWV,...` (wind), `$DPT,...` (depth)

**Integration:** add a second UART on the BoatMon-1 Feather (D11/D12 software UART) reading 0183 from the multiplexer; decode in ESPHome with the [`nmea` external component](https://github.com/esphome/esphome/pull/4287) or via custom lambda for the handful of sentences you care about. Cheap MAX3232/MAX485-based RS-422 → TTL adapter ~$5.

If the only 0183 talker is the chartplotter outputting GPS, this is overkill — just use Path A or B. But if the boat has a legacy 0183-only autopilot, depth, or DSC VHF, this is the path.

---

## 5. Other "Existing Sensor" Integration Patterns

Beyond bus-level integration, EvenKeel can ingest individual existing sensors:

### 5.1 Dry-contact outputs (engine alarm panel, BEP DC monitor, etc.)
- Pattern: same as the bilge float switch — wire to a free GPIO via opto-isolator if voltage is non-3.3V.
- Examples: low-oil-pressure switch, high-water-temp switch, alternator-failure light, engine-room smoke detector.
- ESPHome `binary_sensor:` with `gpio` platform.
- ~$1 in parts per channel.

### 5.2 Victron VE.Direct (text protocol over UART)
- Solar MPPT controllers, Phoenix inverters, BMV battery monitors expose a TX UART line ("VE.Direct port") that emits human-readable key/value pairs at 19200 baud.
- ESPHome support via the **`KinDR/esphome-victron`** external component.
- Requires a $5 VE.Direct → USB cable (Victron part `ASS030530000`) repurposed as TTL by cutting and stripping, or a $3 TTL UART adapter.
- Gives full-resolution Victron data without BLE pairing.

### 5.3 Modbus RTU / RS-485 (industrial sensors)
- Standard in HVAC, marine refrigeration, larger inverters, and many tank-level senders.
- ESPHome native support via **`modbus:`** and **`modbus_controller:`** components.
- Hardware: any MAX485-based ESP32 transceiver board ($3) or a Qwiic Modbus adapter ($15 from SparkFun).
- Catalog: thousands of off-the-shelf temperature, humidity, current, pressure, flow sensors.

### 5.4 J1939 engine bus (newer diesels)
- Modern engines (Yanmar VC10, Volvo D2, Cummins QSD) speak J1939 — a CAN dialect — for RPM, oil pressure, coolant temp, fuel rate, hours.
- Tap with the same hardware as Path A's CAN-ESP32 (same ttlappalainen library decodes both N2K and J1939).
- Confirms RPM and engine-hour automation without an alternator-W tap.

### 5.5 Pulse counting (alternator W terminal — without N2K)
- Same approach the original design proposed — opto-isolator + GPIO pulse counter. Belongs in Phase 11+.

### 5.6 Dry-contact outputs from existing instruments
- Many older marine chartplotters and instruments have dry-contact outputs for "alarm raised" — usable as binary inputs.

---

## 6. Recommended Architecture

A **two-step path** that lands in Path B (SignalK) for the long term while letting Path A be a quick win:

1. **Phase 11a (quick win, $60):** Add a Path A CAN-ESP32 satellite. Decode the 5–10 PGNs that matter most: lat/lon, COG/SOG, depth, wind speed/angle, engine RPM, water temp. Bridge to MQTT.
2. **Phase 11b (when ready, $150):** If/when you find Path A's hand-rolled decoder list growing painful, swap to Path B (SignalK on the Pi + Yacht Devices gateway). The MQTT topics stay the same — HA doesn't notice. Path A ESP32 stays as a backup on the bus.

This means: **start cheap, replace when grown.** No path is wasted; no hardware is orphaned.

For NMEA 0183: only build it if a survey reveals a 0183-only talker that's not on the (presumably more recent) N2K backbone. Don't pre-emptively add the second UART.

---

## 7. Hardware BOM Add-ons

### 7.1 Path A (DIY CAN-ESP32, ~$60)

| Item | $ |
|---|---|
| Waveshare ESP32-S3-CAN-FD board (or ESP32-S3-Touch-LCD-4.3 if combining with Tier 1 panel) | $25 |
| N2K micro tee | $20 |
| 0.5m N2K drop cable | $15 |
| Optional: Yacht Devices YDIM-01 N2K isolator | +$80 |
| **Subtotal (no isolator)** | **$60** |

### 7.2 Path B (commercial gateway + SignalK, ~$185)

| Item | $ |
|---|---|
| Yacht Devices YDNU-02 USB N2K gateway | $150 |
| N2K tee + drop cable | $35 |
| SignalK Server (open source) | $0 |
| **Subtotal** | **$185** |

### 7.3 NMEA 0183 (only if needed)

| Item | $ |
|---|---|
| MAX3232 / MAX485 → TTL adapter | $5 |
| 0183 multiplexer (only if multiple talkers) | $80–120 (Shipmodul MiniPlex, Actisense ANMEA-2) |

### 7.4 Other patterns

| Pattern | $ |
|---|---|
| Dry-contact in via opto-isolator | $1 per channel |
| VE.Direct: Victron cable + TTL adapter | $8 |
| Modbus RTU: MAX485 board | $3 (or Qwiic $15) |

---

## 8. Where This Lands in Sensor-Expansion Tiers

This integration is best thought of as a sixth tier on top of the [five-tier sensor expansion model](sensor-expansion.md):

```
TIER 6 — Integration with existing marine buses & instruments
   ├── 6a. NMEA 2000 (CAN, 250 kbps) — Path A or Path B
   ├── 6b. NMEA 0183 (RS-422 serial)
   ├── 6c. Victron VE.Direct
   ├── 6d. Modbus RTU
   ├── 6e. J1939 engine bus
   └── 6f. Dry-contact outputs from existing instruments
```

Tier 6 is **read-only** by design. EvenKeel publishes nothing back. The chartplotter remains the source of truth for navigation; EvenKeel becomes a *consumer* that pushes the same data into HA dashboards, automations, and historical recording.

---

## 9. What This Buys You — Concrete Examples

If the Hunter has an N2K backbone with chartplotter, depth, and wind:

| Capability | Without Tier 6 | With Tier 6 |
|---|---|---|
| GPS position | Phase 8 hardware ($70 NEO-M9N + antenna) | Free — read from N2K |
| Wind speed/angle | Phase 11+ DIY hall-effect or Davis 6410 ($80) | Free — read from N2K |
| Depth | Future stretch | Free — read from N2K |
| Speed-through-water | Future stretch | Free — read from N2K |
| Engine RPM | Phase 11+ alternator-W tap with optocoupler | Free if engine is on N2K (newer Yanmar) |
| Storm warning via baro trend | BME280 in cabin (already in plan) | Same, plus N2K outdoor pressure if installed |
| Anchor drag detection | Phase 9 GPS-based | Same, but uses chartplotter's GPS |
| AIS targets in HA (currently from dAISy stream_server) | Tier 1 default | Same — N2K AIS PGNs available too as cross-check |
| Course-up / Heading-up dashboard rendering | Not in plan | N2K heading enables it |

**Net effect:** if Tier 6 lands, Phase 8 (GPS hardware) becomes optional rather than required. That's a real $70 + install savings.

---

## 10. Phase Placement

Tier 6 lives in **Phase 11+**, after v1 (Phase 6) ships and after Phase 7–10 prove the foundation. **Don't conflate Tier 6 with v1.** Specifically:

- **Phase 11a — N2K Read (DIY, Path A)**: $60, ~1 weekend, drops in 5–10 PGNs.
- **Phase 11b — SignalK upgrade (Path B)**: $185, optional later step if Phase 11a grows beyond what hand-rolled decoders comfortably handle. Adds free SignalK Kip dashboard.
- **Phase 11c — NMEA 0183 (only if needed)**: ~$5–125 depending on talker count and whether a multiplexer is needed.

Each phase is self-contained, ships working, and costs no more than a weekend of work.

---

## 11. ESPHome / SignalK Topic Conventions

To keep MQTT topics stable across DIY (Path A) and SignalK (Path B), settle on canonical names now:

| EvenKeel MQTT topic | N2K PGN | SignalK path |
|---|---|---|
| `boat/hunter41/nav/lat` | 129025 | `navigation.position.latitude` |
| `boat/hunter41/nav/lon` | 129025 | `navigation.position.longitude` |
| `boat/hunter41/nav/cog` | 129026 | `navigation.courseOverGroundTrue` |
| `boat/hunter41/nav/sog` | 129026 | `navigation.speedOverGround` |
| `boat/hunter41/nav/heading` | 127250 | `navigation.headingTrue` |
| `boat/hunter41/wind/apparent_speed` | 130306 | `environment.wind.speedApparent` |
| `boat/hunter41/wind/apparent_angle` | 130306 | `environment.wind.angleApparent` |
| `boat/hunter41/wind/true_speed` | 130306 | `environment.wind.speedTrue` |
| `boat/hunter41/depth/below_transducer` | 128267 | `environment.depth.belowTransducer` |
| `boat/hunter41/speed/through_water` | 128259 | `environment.speed.throughWater` |
| `boat/hunter41/engine/rpm` | 127488 | `propulsion.main.revolutions` |
| `boat/hunter41/engine/oil_pressure` | 127489 | `propulsion.main.oilPressure` |
| `boat/hunter41/engine/coolant_temp` | 127489 | `propulsion.main.temperature` |
| `boat/hunter41/engine/hours` | 127489 | `propulsion.main.runTime` |
| `boat/hunter41/battery/house/v_n2k` | 127508 | `electrical.batteries.house.voltage` |
| `boat/hunter41/rudder/angle` | 127245 | `steering.rudderAngle` |

Path A's decoder publishes directly to these topics; Path B's `signalk-to-mqtt` plugin maps SignalK paths → MQTT topics via config. Same topics, same HA dashboards.

---

## 12. Update to "Non-Goals"

Original `architecture.md §6` says EvenKeel does NOT replace chartplotters or feed nav data to instruments. That stands.

**Add to non-goals:**
- ❌ Writing to N2K — EvenKeel never transmits on the bus.
- ❌ Acting as a primary source for nav data — chartplotter remains the source of truth.
- ❌ Calibrating instruments via EvenKeel — calibration belongs to the instrument's own UI.

**New permitted scope (Tier 6):**
- ✅ Reading N2K, 0183, J1939, VE.Direct, Modbus traffic for telemetry purposes.
- ✅ Republishing decoded values to HA via the existing MQTT bridge.
- ✅ Using ingested data in HA automations and recorder history.

---

## 13. Open Questions for Pete

| # | Question | Resolve when |
|---|---|---|
| Q40 | Does the Hunter 41DS have an N2K backbone? Is the chartplotter Garmin / Raymarine / B&G — and what era? | At purchase / survey |
| Q41 | What N2K connector type is in use? Maretron Mini? Garmin/NMEA "Micro-C"? Old DeviceNet 5-pin? | At survey |
| Q42 | Is the engine a newer Yanmar with J1939/CAN output, or older mechanical-injection? | Engine plate / serial |
| Q43 | Are there any 0183-only talkers? (DSC VHF, autopilot, fluxgate compass, depth sounder) | At survey |
| Q44 | Path A (DIY $60) or Path B (SignalK $185) for first attempt? | At Phase 11 start |
| Q45 | Is a Victron BMV/SmartShunt or MPPT installed with VE.Direct accessible? | At electrical inspection |
| Q46 | Should Phase 8 GPS hardware ($70) be cancelled if N2K provides GPS? | At Phase 11a exit |
| Q47 | Any safety-critical N2K data (e.g., engine alarm) that should bypass HA and trigger Tier 0 alarm directly? | At Phase 11a |
| Q48 | Should Tier 6 data be tagged in MQTT as `source=n2k` for distinguishing from native EvenKeel sensors? | Topic-convention design |

---

## 14. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Buggy decoder bricks the N2K bus | Low (read-only by design) | Use galvanic isolator on the drop; physically remove drop if anything weird happens |
| N2K backbone is full (max 50 devices) | Low | A read-only listener counts as a load device; verify backbone budget |
| Connector type mismatch (Maretron vs Garmin vs Lowrance Micro-C) | Medium | Buy a multi-connector adapter kit ($15) before committing |
| Ground-loop currents through bus shield | Low | YDIM-01 isolator (+$80) eliminates this |
| ESPHome canbus component instability under heavy bus load | Low | Path A has a 250 kbps shared bus; the ESP32-S3 TWAI is fine to ~1 Mbps. Bench-test before install |
| Path A decoder gets behind protocol updates | Medium | Move to Path B (SignalK) when this happens — that's why Path B is the long-term answer |
| Some PGNs are vendor-proprietary and undocumented | Medium | Ignore them. Decode only well-documented standard PGNs |

---

## 15. References

- **N2K & SignalK ecosystem**
  - SignalK Server: https://github.com/SignalK/signalk-server
  - SignalK to MQTT plugin: https://github.com/SignalK/signalk-to-mqtt
  - NMEA 2000 PGN reference: https://www.nmea.org/Assets/2000_explained_white_paper.pdf
  - Yacht Devices YDNU-02: https://www.yachtd.com/products/usb_gateway.html
  - Yacht Devices YDIM-01 isolator: https://www.yachtd.com/products/isolator_module.html
  - Actisense NGT-1: https://actisense.com/product/nmea-2000-pc-interface-ngt-1/
- **DIY N2K libraries**
  - ttlappalainen/NMEA2000: https://github.com/ttlappalainen/NMEA2000
  - AK-Homberger NMEA 2000 ESP32 examples: https://github.com/AK-Homberger/NMEA2000-Workshop
- **ESPHome integrations**
  - canbus component: https://esphome.io/components/canbus/index.html
  - Modbus components: https://esphome.io/components/modbus_controller.html
  - Victron BLE: https://github.com/Fabian-Schmidt/esphome-victron_ble
  - VE.Direct: https://github.com/KinDR/esphome-victron
- **Hardware**
  - Waveshare ESP32-S3-CAN-FD: https://www.waveshare.com/esp32-s3-can-fd.htm
  - Waveshare ESP32-S3-Touch-LCD-4.3 (with onboard CAN): https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-4.3B
- **HA integration**
  - SignalK ↔ HA: https://github.com/SignalK-HA/home-assistant-signalk

---

## 16. Where This Lives in the Plan

- [`architecture.md §2.6.5`](architecture.md) — already references Tier 1–5; add Tier 6 reference
- [`sensor-expansion.md`](sensor-expansion.md) — add Tier 6 callout
- [`roadmap.md`](roadmap.md) — Phase 11+ adds N2K read sub-phases (11a, 11b, 11c)
- [`open-questions.md`](open-questions.md) — Q40–Q48 above to be added in §0 or §C-Hardware
- [`hardware-deep-dive.md §H.5`](hardware-deep-dive.md) — Tier 6 BOM additions (Path A and B)
