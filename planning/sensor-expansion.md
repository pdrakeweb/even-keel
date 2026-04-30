# EvenKeel — Sensor Expansion Architecture

**Question:** Can the simplified Feather + Qwiic design accept 5, 10, 20+ more sensors of various kinds without re-architecting?
**Answer:** Yes — through a five-tier expansion model where each tier is plug-together and costs $5–25 to add. You never re-design the boat node; you reach into the appropriate tier.

---

## TL;DR — Pick a tier

```
                         distance from BoatMon-1
                              ⬆
                          mast / dinghy / off-boat
   Tier 5 — Wireless     ────────────────────────────
   (BLE, Zigbee, LoRa)         remote, battery, mobile
                          ────────────────────────────
   Tier 4 — Satellite          per-locker, far-bilge, V-berth
   ESP32 nodes               ────────────────────────────
                                cabin-wide / engine-room
   Tier 3 — 1-Wire bus       (temp only)
   (DS18B20 daisy chain)     ────────────────────────────
                                cabin areas, multiple zones
   Tier 2 — Multiplexed I²C   (any I²C sensor, expanded address space)
   (TCA9548A Qwiic mux)      ────────────────────────────
                                local to nav station
   Tier 1 — Direct Qwiic       (3-5 sensors, ≤1m)
   chain                     ────────────────────────────
                              ⬇
                              BoatMon-1 Feather
```

| Tier | Best for | Sensors per tier | Distance | $ per sensor |
|---|---|---|---|---|
| 1 | Local I²C cluster | 3–5 | ≤1m | $5–15 |
| 2 | Mux-expanded I²C, same-type duplicates | up to 64 (mux + sub-muxes) | ≤2m | $5–15 + $7 mux |
| 3 | Temperature anywhere on the boat | up to 30 DS18B20 | ≤50m | $8 |
| 4 | Sensor cluster in a remote locker | unlimited (more nodes) | unlimited | $15–25 + sensors |
| 5 | Battery / mobile / off-boat | unlimited | LoRa to km | $5–50 |

---

## Tier 1 — Direct Qwiic chain (the v1 default)

This is what's already in the BOM. Three sensors today; up to ~5–8 before you start hitting limits.

**What you can add today (just plug in another STEMMA QT cable):**

| Sensor | Adafruit # | I²C addr | What it does |
|---|---|---|---|
| BME280 / BME680 | #2652 / #3660 | 0x76 / 0x77 | T + RH + baro (+ VOC for 680) |
| SHT40 / SHT41 | #4885 / #5776 | 0x44 | High-accuracy T + RH |
| BMP390 | #4816 | 0x77 | Better baro than BME280 |
| SCD41 | #5190 | 0x62 | Real CO₂ (cabin air quality) |
| LTR-559 | #5591 | 0x23 | Ambient light + proximity |
| ICM20948 | #4554 | 0x69 | 9-DOF IMU (heel, pitch, motion) |
| INA260 / INA228 | #4226 / #5832 | 0x40 | More current shunts |
| VEML7700 | #4162 | 0x10 | Lux meter (for auto night-mode) |
| MCP9808 | #1782 | 0x18 | High-precision temperature |
| LSM6DS33 | #3463 | 0x6A | Accel + gyro (slap-of-water detect) |

**Where Tier 1 stops:**

- **Address conflicts.** Two BME280s on the same bus collide unless one has its `SDO` jumper soldered (changes 0x76 → 0x77). Three or more = fail.
- **Bus length.** Qwiic spec recommends ≤1m at 100 kHz. Most builds work at 2m, get sketchy past 5m.
- **Pull-up loading.** Each board has 10 kΩ pull-ups; >5 boards in parallel weakens drive strength. (Adafruit boards have cuttable jumpers to disable; SparkFun usually ships them disabled by default — read the silkscreen.)

When you hit any of these, jump to Tier 2.

---

## Tier 2 — Multiplexed I²C (TCA9548A Qwiic mux)

A 1-to-8 I²C multiplexer. Each of its 8 channels is a *separate* I²C bus, electrically isolated. Means you can run 8 BME280s without changing addresses, or 8 separate cable runs to different lockers. Can cascade muxes for 64+ channels.

**Hardware:**
- Adafruit TCA9548A Qwiic mux — #2717, **$7**
- Has 8× STEMMA QT outputs + 1× input
- ESPHome supports it natively as `i2c_multiplexer:`

**Wiring:**
```
[Feather STEMMA QT]──→[TCA9548A mux input]
                          │
                          ├─ ch0 ──→ [BME280 #1, cabin]
                          ├─ ch1 ──→ [BME280 #2, lazarette]
                          ├─ ch2 ──→ [BME280 #3, V-berth]
                          ├─ ch3 ──→ [BME280 #4, head]
                          ├─ ch4 ──→ [INA228 #2, alternator current]
                          ├─ ch5 ──→ [SCD41 cabin CO₂]
                          ├─ ch6 ──→ [VEML7700 cockpit lux]
                          └─ ch7 ──→ [TCA9548A #2 → 8 more channels]
```

**ESPHome config sketch:**
```yaml
i2c:
  sda: GPIO3
  scl: GPIO4

i2c_multiplexer:
  - id: cabin_mux
    address: 0x70
    channels:
      - bus_id: cabin_bus
        channel: 0
      - bus_id: lazarette_bus
        channel: 1
      # ...

sensor:
  - platform: bme280_i2c
    i2c_id: cabin_bus
    temperature: { name: "Cabin temp" }
    humidity:    { name: "Cabin RH" }
  - platform: bme280_i2c
    i2c_id: lazarette_bus
    temperature: { name: "Lazarette temp" }
```

**Cascade for more:** plug a second TCA9548A into one channel → 7 + 8 = 15 effective channels. Repeat to your heart's content. Practical limit is the host MCU's I²C handling at 64+ devices, which the ESP32-S3 handles fine.

**Cost to add 8 humidity zones:** $7 mux + 8× $5 SHT40 = **$47 total**, plus 8× STEMMA QT cables ($1–3 each).

---

## Tier 3 — 1-Wire bus (temperature only, but huge reach)

DS18B20 sensors are addressable by 64-bit ROM, can chain dozens, and tolerate **long cable runs** — 50m+ in real-world boat installations.

**Why it's the right answer for "more temperatures":**

- Each DS18B20 has a unique factory-burned ID. You can put 30 on one wire and ESPHome auto-discovers them.
- Three-conductor wiring (3.3V / data / GND), or two-wire parasite power.
- One 4.7 kΩ pullup near the BoatMon-1 — that's it.
- Pre-wired waterproof probes with 1m, 3m, or 6m leads, ~$8 each.

**Wiring topologies:**

```
"Daisy-chain" (preferred):
  BoatMon-1 ──┬── probe1 ──┬── probe2 ──┬── probe3 ──┬── probe4 ──...
                                                        (terminated)

"Star" (each probe has its own home run, joined at a hub):
  BoatMon-1 ──┬── probe1
              ├── probe2
              ├── probe3
              └── probe4
   ⚠ Star with long arms can have reflection issues; daisy is safer.
```

**Pre-built RJ12 hubs** for clean star topology: Hobby Boards "1-Wire Hub" RJ12-style adapter ($20–35) lets each probe plug into a phone-jack-style splitter — **fully solderless** for the temperature subsystem.

**ESPHome config — adds zero extra code per sensor:**
```yaml
one_wire:
  - platform: gpio
    pin: GPIO6

sensor:
  - platform: dallas_temp
    address: 0x1234567890abcdef
    name: "Cabin temp"
  - platform: dallas_temp
    address: 0xfedcba0987654321
    name: "Engine bay temp"
  # add as many as you have probes;
  # `esphome run --device <ip> --logs` shows discovered ROM IDs on first boot
```

**Realistic boat coverage with Tier 3 alone:**
cabin · v-berth · head · galley · nav station · engine bay · engine intake · refrigerator · freezer · lazarette · quarter berth · bilge · fuel tank · holding tank · water tank — **15 zones, all from one GPIO + one pullup, ≤$120 total in probes.**

---

## Tier 4 — Satellite ESP32 nodes (per-locker, per-zone)

When a sensor cluster is far from the central node — say, the masthead or a remote locker — running a long Qwiic or 1-Wire cable becomes impractical. Instead: deploy a tiny secondary ESP32 that handles its local sensors and publishes via WiFi MQTT to the boat broker. The boat-side architecture treats it identically to BoatMon-1.

**Hardware options for the satellite:**

| Board | $ | Why |
|---|---|---|
| **Adafruit QT Py ESP32-S3** | $15 | Tiny (1"×0.7"), STEMMA QT onboard, USB-C, headers optional |
| **Seeed XIAO ESP32-C3** | $5 | Cheapest credible ESP32; surprisingly capable |
| **M5StickC Plus 2** | $25 | Has a screen + battery + IMU; great for "what's it doing in the lazarette" |
| **Adafruit ESP32-S3 Reverse TFT Feather** | $25 | If you want a built-in display at the satellite location |

**What a satellite looks like:**

```
┌────────────────────────────────────────┐
│ Satellite "BoatMon-Lazarette"           │
│                                          │
│  QT Py ESP32-S3 (with USB-C + Qwiic)    │
│  ├─ Qwiic SHT40 (T + RH)                │
│  ├─ Qwiic SCD41 (CO₂)                   │
│  └─ DS18B20 1-Wire (deep-locker temp)   │
│                                          │
│  Powered: 5V from boat USB outlet OR    │
│           LiPo + solar trickle (Phase 11)│
│                                          │
│  Comms: WiFi → boat broker MQTT          │
│  Topics: boat/hunter41/lazarette/*       │
└────────────────────────────────────────┘
```

**ESPHome config** is its own file (`firmware/satellites/lazarette.yaml`); it joins the boat WiFi, publishes to the same broker. HA auto-discovers via MQTT.

**Failure isolation bonus:** if a satellite's USB cable gets pinched and the node dies, BoatMon-1 keeps running. HA marks just the lazarette entities as offline.

**Practical fleet examples:**

| Satellite | Sensors | Cost |
|---|---|---|
| Lazarette | T/RH, CO₂, water-leak switch | $35 |
| V-berth | T/RH, motion (intrusion) | $25 |
| Engine compartment "deep" | engine intake T, oil-pressure switch, alternator W RPM | $30 |
| Mast base | wind direction, wind speed (Davis or DIY hall) | $80 |
| Solar charge controller area | CT clamp, panel V | $25 |

You can keep adding satellites indefinitely. **Each is independent.** Each is configured by editing a single YAML file at home and pushing OTA via WireGuard.

---

## Tier 5 — Wireless sensor ecosystems (already-built, batteries included)

For sensors that should be wireless because wiring is impossible or undesirable — or for sensors where you'd rather buy than build.

### 5a. BLE — Bluetooth Low Energy
- Already used: Victron SmartShunt, MPPT, BMV (Phase 7).
- Add: **RuuviTag** ($35) — outdoor-rated, 5+ year battery, T/RH/baro/motion. Toss one in any locker.
- Add: **Govee H5179** fridge thermometer ($15) — battery-powered, BLE, ESPHome can read advertisements.
- Range: ~10–30m through fiberglass.
- Configured via `esp32_ble_tracker` in ESPHome.

### 5b. Zigbee — via Sonoff ZBDongle-E on the Pi
- One-time hardware: **Sonoff ZBDongle-E** ($20) plugged into the boat Pi.
- Opens the **entire Zigbee2MQTT catalog** (3000+ devices): Aqara, IKEA Tradfri, Sonoff, Tuya.
- Examples:
  - **Aqara T1 contact sensor** ($12) — hatches, lockers, head door open/close
  - **Aqara water leak sensor** ($15) — drop in head, galley, engine drip pan
  - **Aqara T1 motion sensor** ($18) — V-berth occupancy, intrusion
  - **Aqara T+H sensor** ($15) — battery T/RH for any locker
- 100m+ mesh range; battery lasts ~2 years.
- HA integration is one-click via ZHA or Z2M add-on.

### 5c. LoRa — for ultra-long-range
- For things genuinely off the boat: **dinghy tracker**, **anchor buoy** with depth+drift sensor, **mooring camera at distance**.
- Hardware: **Heltec WiFi LoRa 32 V3** ($20) on each end.
- Range: kilometers in line of sight, hundreds of meters in marina.
- Lower data rate; suited to "is the dinghy here?" not "stream HD video."

---

## Decision tree — picking a tier

```
Is the new sensor within 1m of BoatMon-1?
│
├─ Yes → Is it I²C and unique address? ──Yes──→ TIER 1 (just plug in)
│                                       └─No──→ TIER 2 (mux it)
│
└─ No → Is it temperature only, ≤50m? ──Yes──→ TIER 3 (1-Wire daisy)
        │
        └─ No → Is it a cluster in one location? ──Yes──→ TIER 4 (satellite)
                │
                └─ No → Wireless / battery / off-boat?
                        ├─ short range, mostly fixed → TIER 5b (Zigbee)
                        ├─ medium range, off-the-shelf → TIER 5a (BLE)
                        └─ very long range, custom → TIER 5c (LoRa)
```

---

## Naming and topic conventions for expansion

Whatever tier a sensor lands in, MQTT topics follow:

```
boat/hunter41/<category>/<zone>/<metric>
```

Examples:
- `boat/hunter41/temp/cabin` (Tier 3, DS18B20)
- `boat/hunter41/temp/v_berth` (Tier 3)
- `boat/hunter41/humidity/lazarette` (Tier 4 satellite via Tier 1 BME280)
- `boat/hunter41/co2/cabin` (Tier 1, SCD41)
- `boat/hunter41/contact/forepeak_hatch` (Tier 5b, Aqara)
- `boat/hunter41/leak/head` (Tier 5b)
- `boat/hunter41/wind/speed` (Tier 4 mast satellite)

Topic strings are just labels — you're free to invent zones and metrics. HA's MQTT discovery + entity naming follows them automatically. Establish the convention once in [`firmware/packages/conventions.yaml`](../firmware/packages/conventions.yaml) and stick to it.

---

## Cost to expand from v1 ship gate to "well-instrumented boat"

Realistic upgrade path post-Phase 6:

| Add-on | Tier | Cost |
|---|---|---|
| 7 more DS18B20 probes (full 10-zone temp) | 3 | $56 |
| TCA9548A mux + 4 BME280 (humidity in 4 lockers) | 2 | $27 |
| SCD41 cabin air quality | 1 | $50 |
| Lazarette satellite (QT Py + 2 sensors) | 4 | $35 |
| Mast wind satellite (QT Py + Davis) | 4 | $80 |
| Sonoff ZBDongle-E on Pi | 5b | $20 |
| 5× Aqara contact sensors (hatches, lockers) | 5b | $60 |
| 3× Aqara water leak sensors (head, galley, engine) | 5b | $45 |
| RuuviTag (battery T/RH for one locker) | 5a | $35 |
| **Total to ~30 distinct sensors** | mixed | **~$408** |

A **30-sensor boat** for under **$410 over and above the v1 ship-gate** ($535). All plug-together. No re-architecture.

---

## ESPHome / HA capacity

Often the silent question: "Will the firmware actually handle this?"

- **Single Feather:** comfortably handles 30+ sensors across all tiers it directly serves. RAM usage ~120 KB at 30 entities; PSRAM never touched.
- **MQTT topic count:** boat broker handles thousands of topics on a Pi 4 without breaking a sweat.
- **HA recorder:** default SQLite handles ~50–100 entities at 1-min sample rate for years; switch to MariaDB or InfluxDB add-on if you cross 200 entities or want long retention.
- **Wokwi simulator:** scales fine for testing — each sensor adds one or two YAML lines and a few KB of test data.

---

## Pre-built kits worth knowing about

| Kit | Vendor | $ | What's inside |
|---|---|---|---|
| **STEMMA QT/Qwiic Sensor Pack** | Adafruit | $40–60 | Variety pack of T/RH/baro/lux/IMU on STEMMA |
| **SparkFun Qwiic Starter Kit** | SparkFun | $50 | Same idea, different brand |
| **Seeed Grove Sensor Pack** | Seeed | $40 | 12 sensors, but Grove (4-pin) needs a Grove-to-Qwiic adapter ($3) |
| **Aqara Starter Kit** | Aqara / Amazon | $80 | Hub + 5 sensors (use HA's Zigbee instead of their hub — drops to ~$60 for the sensors alone) |
| **RuuviTag 4-pack** | Ruuvi | $130 | Four outdoor-rated BLE sensors |

---

## Where this lands in the EvenKeel design

This expansion model **doesn't change anything in the v1 BOM**. It only changes what's *possible* in Phase 10 and beyond. The Feather + Qwiic + Pi-broker architecture was specifically chosen so that:

- Tiers 1–3 are first-class on day one.
- Tier 4 reuses the same firmware repo, same MQTT broker, same HA dashboards.
- Tier 5 reuses HA's existing ecosystem at zero firmware cost.

Each tier is mature enough that no R&D risk lives here. It's plug-together, all the way up.

---

## Tier 6 — Existing-bus integration (NMEA 2000 / 0183 / VE.Direct / Modbus / J1939)

Beyond *adding* sensors, EvenKeel can *tap into* the boat's existing instrumentation — chartplotter, autopilot, depth, wind, engine bus, Victron solar — without installing duplicate hardware. **Read-only by design.**

**Detail:** [`nmea2000-integration.md`](nmea2000-integration.md).

| Sub-tier | Bus | DIY $ | Commercial $ |
|---|---|---|---|
| 6a | NMEA 2000 (CAN, 250 kbps) | $60 (CAN-ESP32) | $185 (Yacht Devices YDNU-02 + SignalK) |
| 6b | NMEA 0183 (RS-422 serial) | $5 (MAX3232 adapter) | $80–125 (multiplexer if multiple talkers) |
| 6c | Victron VE.Direct | $8 (cable + TTL) | — |
| 6d | Modbus RTU / RS-485 | $3 (MAX485) | $15 (Qwiic) |
| 6e | J1939 engine bus | $25 (same hardware as 6a) | — |
| 6f | Dry-contact outputs | $1 per channel | — |

**What this buys you on a typical Hunter 41DS:**
- GPS position (replaces Phase 8's $70 hardware if chartplotter is on the bus)
- Wind speed/angle
- Depth below transducer
- Speed through water
- Engine RPM, hours, fuel rate (if newer Yanmar with J1939)
- Solar MPPT data (if Victron with VE.Direct)
- AIS targets cross-check

**Phase placement:** 11a (DIY $60) → 11b (SignalK upgrade $185 if/when needed) → 11c (NMEA 0183 only if specific 0183 talkers exist).

---

## See also

- [`hardware-deep-dive.md §C`](hardware-deep-dive.md) — sensor catalog
- [`diagrams/hardware.md §6`](diagrams/hardware.md) — current sensor wiring
- [`diagrams/hardware-visuals.html`](diagrams/hardware-visuals.html) — to be updated with expansion topology diagram
- ESPHome i2c_multiplexer: https://esphome.io/components/i2c.html#i2c-multiplexer
- ESPHome dallas_temp: https://esphome.io/components/sensor/dallas_temp
- ESPHome esp32_ble_tracker: https://esphome.io/components/esp32_ble_tracker
- Zigbee2MQTT supported devices: https://www.zigbee2mqtt.io/supported-devices/
