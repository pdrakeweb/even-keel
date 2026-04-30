# EvenKeel — Hardware, Sensor, and Actuator Deep Dive (v1.1)

> **⚠ PARTIALLY SUPERSEDED by [`simplicity-review.md`](simplicity-review.md) (April 2026).**
> The simplicity review replaces Sections C (sensor breakouts), E (power subsystem), F (enclosure), and parts of G (connectors) with a simpler plug-together approach using Adafruit Feather + STEMMA QT/Qwiic, externalized USB-C power (Scanstrut), and Shelly smart plugs for AC detection.
> Still authoritative: Sections A (MCU tradeoffs), B (AIS receiver), D (engine runtime), H (actuator safety), I (availability).

**Purpose:** Validate and extend the v1.0 design BOM (`research/sailboat-monitor-design.md` §9, §10, §17), add v2 actuator scope, and answer sourcing/availability questions.
**Target vessel:** Hunter 41DS, Lake Erie (Safe Harbor Sandusky).
**Date:** April 2026. Prices in USD, quantities for a single-boat build.

---

## A. Core MCU tradeoffs

**Recommendation: keep the ESP32-S3-DevKitC-1-N16R8V.** The nominated part is still the right call for EvenKeel, but I want to document *why* so we don't drift when tempted by the shinier ESP32-C6/RP2350.

| Candidate | Flash/PSRAM | WiFi | BLE | Thread/Zigbee | ESPHome status | Best for EvenKeel? |
|---|---|---|---|---|---|---|
| **ESP32-S3-DevKitC-1-N16R8V** | 16 MB / 8 MB PSRAM | 2.4 GHz 802.11 b/g/n | BLE 5.0 (long-range, 2 Mbps) | No | Tier-1 stable | **Yes — primary** |
| ESP32 (classic WROOM-32) | 4 MB / 0 | 2.4 GHz | BT Classic + BLE 4.2 | No | Tier-1 stable | Adequate, but no PSRAM caps AIS+MQTT+TCP buffers |
| ESP32-S2 | 4 MB / varies | 2.4 GHz | **No BLE** | No | Tier-1 stable | Disqualified — Victron needs BLE |
| ESP32-C6 | 8 MB / 0 | WiFi 6, 2.4 GHz | BLE 5.3 | Thread 1.3 + Zigbee | Tier-2 (OpenThread in 2025.6+, still being refined per release notes) | Not yet. Thread/Matter is Phase-12+ territory; today it buys a churny toolchain for no v1 win |
| RP2350 (Pico 2 W) | 4 MB external / 520 KB SRAM | 2.4 GHz (CYW43) | BLE 5.2 | No | Verified in ESPHome 2026.3.0 (March 2026), still young | Weaker external-component ecosystem; no PSRAM path to hold large AIS/stream buffers; skip |

**Why S3 specifically for EvenKeel:**
1. **BLE is load-bearing** for Phase 7 (Victron SmartShunt). C3/S3/original ESP32 all have BLE; S2 and RP2350 do not / only-just-do.
2. **PSRAM matters.** Stream-server + MQTT + TLS + potential GPS NMEA parsing sits comfortably in 8 MB PSRAM; on a plain ESP32, TLS handshakes under WiFi pressure are where OOMs show up.
3. **Dual UART + plenty of ADC** pins without juggling — dAISy on UART1, GPS on UART2, ADC1 for voltage divider, I²C on any pair.
4. **Native USB-C** on DevKitC-1 — flash and power on one cable, critical for the 12V→USB-C→bank→USB-C-DevKit chain.
5. **N16R8V is the `-V` (3.3 V internal LDO flash) variant** — needed because the -1 board's USB-C input goes through its own regulator; the V variant tolerates the on-board VBUS regulator better than the non-V.

**Alternative worth keeping on the shelf:** an **ESP32-S3-WROOM-1-N16R8 module soldered to a custom carrier** in a future v2 if we ever go to a PCB. For v1, the DevKitC-1 is the right "no-custom-PCBs" part.

- <https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-DEVKITC-1-N16R8V/> — ~$17
- <https://www.espressif.com/en/products/devkits>

---

## B. AIS receiver alternatives to dAISy HAT

**Recommendation: keep dAISy HAT.** No finalist matches its UART-simplicity, dual-channel sensitivity, and $75 price. Alternatives either cost more, add unnecessary WiFi/GPS stacks we already handle, or have worse sensitivity.

| Receiver | Channels | Sensitivity | Interface | Price | UART integration | Notes |
|---|---|---|---|---|---|---|
| **Wegmatt dAISy HAT** | Dual (A+B) | ~−107 dBm (best-in-class at $75) | 3.3 V TTL UART 38400 (three pads: 3V3/GND/TX) | $75 | **Trivial** — one wire + common ground | Tier-1 recommendation |
| Wegmatt dAISy USB (Tindie) | Dual | ~−107 dBm | USB (CDC-ACM) | ~$70 | Requires USB host support on MCU; ESPHome USB-host not production-ready | Disqualified for ESP32 ESPHome |
| Wegmatt dAISy 2+ | Dual | ~−107 dBm (same front-end) | NMEA 0183 RS-422 + USB | $159 | Needs RS-422→TTL level shifter | Overkill, built for plug-in-to-chartplotter use |
| NASA AIS Engine 3 | Single (time-sliced) | ~−100 dBm | NMEA 0183 RS-232/RS-422, 38400 | ~$170 | Single-channel is a real penalty in a busy harbor; RS-232 level shift required | Skip |
| Quark-Elec QK-A026 | Dual | −105 dBm @ 30% PER | WiFi + USB + RS-422 + integrated GPS | ~$120 | Double-integrates features we're already building; no clean UART-only mode | Overbuilt; skip |

**Rank (price + ease of ESPHome UART integration + sensitivity):**
1. **dAISy HAT — $75, UART TTL, dual-channel, best $/dB.**
2. dAISy 2+ — $159, same chip, adds conveniences we don't need.
3. QK-A026 — $120, feature-rich but wrong shape for our architecture.
4. NASA AIS Engine 3 — $170, worst sensitivity, single-channel time-sliced.

- dAISy HAT: <https://shop.wegmatt.com/products/daisy-hat-ais-receiver>
- dAISy 2+: <https://shop.wegmatt.com/products/daisy-2-dual-channel-ais-receiver-with-nmea-0183>
- QK-A026: <https://www.quark-elec.com/product/a026-wireless-ais-gps-receiver/>
- NASA AIS Engine 3: <https://www.nasamarine.com/product/ais-engine-3/>

---

## C. Sensor-by-sensor deep dive

### C.1 Temperature

| Sensor | Zone | Interface | Addr/Bus | ESPHome | Unit $ | Notes |
|---|---|---|---|---|---|---|
| **DS18B20** (waterproof, 1 m lead) | Engine bay, fridge, bilge, lazarette, any single-point | 1-Wire | 64-bit ROM, any pin | `dallas_temp` | $6–8 | Best for single-temp zones; parasite power supported; add 4.7 kΩ pullup near ESP32, one pullup for the bus |
| **SHT40** (Adafruit 4885) | **Cabin ambient** | I²C | 0x44 (fixed) | `sht4x` | $5 (Sensirion) / $10 (Adafruit) | ±0.2 °C, ±1.8% RH — the right cabin-air sensor |
| **BME280** | Any single location that also needs pressure | I²C | 0x76 / 0x77 | `bme280_i2c` | $8 Adafruit breakout / $3 bare | Humidity accuracy is mediocre (drifts ~15% RH in practice) — use for barometric pressure primarily |
| **BMP390** | Barometer-only for storm warning | I²C | 0x77 | `bmp3xx` | $10 | ±3 Pa — better pressure stability than BME280 over time |
| DHT22 / AM2302 | Cheap fallback | 1-wire (non-standard) | — | `dht` | $5 | **Do not use** on this boat — slow, drifty, no re-read robustness |

**Recommended v1 temperature set (6 sensors for Phase 5):**

- 3× DS18B20: engine compartment, refrigerator, outdoor/cockpit locker
- 1× SHT40 in cabin (temp + humidity — feeds mold-risk automation)
- 1× BMP390 anywhere dry (barometric pressure for storm-warning automation)
- 1× DS18B20 at the enclosure itself (self-temperature, risk mitigation NF-1)

**Phase 10 expansion:** 6 more DS18B20 (head, v-berth, fridge #2, nav station, lazarette, engine raw-water outlet).

- Adafruit SHT40 4885: <https://www.adafruit.com/product/4885>
- Adafruit BMP390 4816: <https://www.adafruit.com/product/4816>
- DS18B20 1m lead: <https://www.adafruit.com/product/381>

### C.2 Battery voltage and current

| Choice | What it gives | When to use | $ | Notes |
|---|---|---|---|---|
| **Victron SmartShunt 500A/50mV IP65** (SHU065150050) | SoC, V, A, time-to-go, history — all via BLE | **House bank** — gold standard | $110–115 | Phase 7 dependency; ESP32 reads via `victron_ble` external component |
| **INA226 breakout + 75 mV shunt** | V + A, 16-bit | Starter bank OR secondary house sense | $12 (breakout) + $8 (50 A shunt) | ±0.5% typical; ESPHome `ina226`; I²C 0x40–0x4F |
| INA228 breakout | Same + 20-bit ADC + energy/charge accumulation | Only if we need energy-over-time without HA math | $25 | Supported in ESPHome via `latonita/esphome-ina228` external or newer `ina2xx_i2c`; 20-bit overkill for battery bank |
| Voltage divider (100 kΩ + 33 kΩ, 1%) + ESP32 ADC1 | V only, ~1% | **Starter battery V only** — cheapest | $0.30 | Existing design choice; keep |

**Recommendation:**
- **House bank:** Victron SmartShunt IP65 500A over BLE. This is Phase 7, and it's the right answer — we get Coulomb counting for free and don't have to install an ESP32-side shunt in a high-current path.
- **Starter battery:** divider-only for V. One channel of ADC1. No current sense needed (engine starts are short, irrelevant for SoC).
- **If SmartShunt isn't in budget:** INA226 with a 500 A / 75 mV shunt from the ship's chandlery; wire directly at the bank's negative post. This is an OK fallback but loses the Victron SoC algorithm.

- Victron SmartShunt IP65 500A: <https://www.victronenergy.com/battery-monitors/smart-battery-shunt>, <https://powerwerx.com/victron-shu065150050-smartshunt-ip65-500a>
- ESPHome INA2xx: <https://esphome.io/components/sensor/ina2xx/>

### C.3 AC detection (shore and genset)

| Option | Principle | Isolation | ESPHome | $ | Verdict |
|---|---|---|---|---|---|
| **HiLetgo 120 V AC→5 V opto-isolator module** | Rectified AC→optocoupler LED | Yes (LED-photodiode) | `binary_sensor` on GPIO | $6–8 | **Keep for shore and genset binary present/absent** |
| ZMPT101B voltage sensor | Mains-frequency transformer + op-amp + RMS in firmware | Yes (magnetic) | external component `hugokernel/esphome-zmpt101b`, or ADS1115 + template | $3–8 | Use only if we want actual voltage reading (brownout detection etc.) |
| ZMCT103C current transformer (5 A/5 mA) | Clamp around one AC conductor | Yes | ADS1115 + template RMS | $5 | Good for confirming genset is actually producing load, not just spinning |
| ACS712 Hall-effect | Inline current | **No — not isolated from primary** | ADC | $3 | **Do not use for AC mains.** Fine for DC side. Safety risk otherwise. |

**Recommendation:**
- Shore: HiLetgo opto. Binary.
- Genset: HiLetgo opto on the genset leg (not shore-inlet leg) for presence. Optional ZMCT103C around genset L1 for actual load — useful diagnostic, not v1.
- **Never inline ACS712 on 120 VAC.** It's a Hall-effect sensor *on* the conductor — its isolation rating is insufficient for mains.

### C.4 Bilge

| Sensor | Type | ESPHome | $ | Notes |
|---|---|---|---|---|
| **Rule-A-Matic Plus (part 35A)** | Caged float, SPST NO | GPIO binary_sensor, internal pullup | $28 | Primary water-present switch — proven on Great Lakes boats |
| Johnson Ultima Senior | Air pressure float alt | GPIO binary | $45 | More failure-tolerant in oily bilges; expensive |
| **JSN-SR04T-V3.0** | Ultrasonic 25–600 cm, waterproof head | `ultrasonic` platform | $10 | V3.0 needs M1 shorted or 47k resistor for trigger/echo mode; continuous level (stretch) |
| Capacitive level strip | Continuous | ADS1115 + template | $15 | Interesting for fuel/water tanks; skip for bilge (fouling) |

**Recommendation as in v1.0: Rule-A-Matic Plus for v1 binary; JSN-SR04T-V3.0 added in Phase 11 for continuous.** Mount the ultrasonic head ~60 cm above the bilge floor (min range is 25 cm) and echo will stay clean of normal slosh.

- Rule-A-Matic Plus: <https://defender.com/en_us/rule-a-matic-plus-float-switch>
- JSN-SR04T in ESPHome: <https://esphome.io/components/sensor/jsn_sr04t/>

### C.5 GPS

| Module | Constellations | Accuracy | Interface | $ | Verdict |
|---|---|---|---|---|---|
| **u-blox NEO-M9N (SparkFun GPS-15210)** | GPS+GLONASS+Galileo+BeiDou concurrent | 1.5 m CEP | UART + I²C + SPI | $75 on breakout | **Primary pick** — SAW+LNA front end survives marina RF; ESPHome `gps` native |
| u-blox NEO-M8N | GPS+GLONASS+Galileo (3 concurrent) | 2.5 m CEP | UART + I²C | $30–40 (SparkFun / generic) | Fine fallback if M9N unavailable |
| ATGM336H | GPS+BDS | 2.5 m CEP | UART | $8 | Ubiquitous AliExpress module; no SAW+LNA — don't trust it in a mast-top SAW-filtered environment |
| Existing NMEA2000 GPS bridge | N/A | N/A | CAN | — | Defer — adds an NMEA2000 interface (MCP2515 or similar) for one datum we already get |

**Recommendation: NEO-M9N on SparkFun GPS-15210 breakout with a 28 dB active patch antenna mounted high.** $75 module + $15 antenna + $5 SMA cable. Phase 8.

- SparkFun GPS-15210: <https://www.sparkfun.com/products/15210>
- ESPHome gps: <https://esphome.io/components/sensor/gps/>

### C.6 Tanks

| Method | Hunter 41DS likely fit | Cost | Verdict |
|---|---|---|---|
| **Existing resistive senders (US 240–33 Ω) + ADS1115 + ~220 Ω pullup to 3.3 V** | Very likely already fitted on fuel & water tanks | $15 | **Do this first.** Phase 8. |
| Capacitive retrofit strip (Gobius C or equiv.) | External attach to tank wall | $200+ per tank | Only if resistive sender is broken or missing |
| Ultrasonic top-mount (JSN-SR04T / SR04M-2) | Freshwater tank with removable inspection port | $10 | Cheap, but fuel-tank top-mount is a fire-code discussion |

**Recommendation:** ADS1115 + lookup table per tank. Budget 4 channels: fresh, holding, diesel, optional gasoline dinghy tank. Single 16-bit ADC breakout at ~$15.

- Adafruit ADS1115 1085: <https://www.adafruit.com/product/1085>

### C.7 Wind (future / stretch)

| Option | Notes | $ |
|---|---|---|
| **Davis 6410 anemometer** | Reed-switch speed + Hall direction; hackable to ESP32 via pulse-counter + ADC | ~$180 |
| DIY hall-effect + 3D-printed cups | Flat-top mount, no mast wiring | $15 + time |
| Existing B&G / Raymarine masthead + NMEA0183 tap | Least invasive if the Hunter has working mast electronics | $0 (software) |

Skip for v1. If Phase 12+ adds wind, Davis 6410 is the reference DIY design.

### C.8 Humidity / mold risk

- **SHT40 × 3** at cabin / v-berth / lazarette on a single I²C bus with TCA9548A multiplexer (address conflict workaround — SHT40 is a single-address part).
- Adafruit TCA9548A 2717: <https://www.adafruit.com/product/2717>. $7. Needed only once to give us 8 branches.
- Automation: publish dewpoint; alert if cabin RH > 75% for 6 h *and* boat is unoccupied (shore power on, no AIS motion).

### C.9 Cabin smoke / CO

ESPHome-compatible choices are thin. The marine correct answer is a **certified, self-powered CO alarm (Fireboy-Xintex CMD-5)** installed independently, and **just read its alarm contact into a GPIO**.

| Sensor | Type | ESPHome support | Verdict |
|---|---|---|---|
| **Fireboy-Xintex CMD-5M** (UL 2034 / ABYC A-24) | CO alarm with NC/NO relay output | GPIO binary_sensor | **Recommended.** $90. Independent power, certified, talks to ESP32 only via dry contact |
| MQ-2 / MQ-7 (smoke / CO) | Analog MOS sensor | `mq` / `template` with ADS1115 | **Not safety-certified** — nice-to-have, not the alarm |
| MH-Z19B (CO₂ not CO) | NDIR | `mhz19` native | Useful for "is the cabin ventilated?", not life-safety |

**Rule:** do not rely on a DIY sensor for life-safety. Ingest the certified alarm's contact; use MQ-2 only as an informational secondary.

### C.10 Water-in-fuel

**Recommended: Racor RK23191-01 WIF probe + a simple 12 V alarm module tapped with an opto-isolator to GPIO.** Racor's own 2-wire WIF probes detect water at the bottom of the Racor filter bowl via resistance change. Pair with the RK-12870 LAK-1 kit (12 V audio/visual) and tee its "alarm" output through an opto-isolator to the ESP32.

- Racor RK23191-01 probe: <https://www.racorstore.com/racor-rk23191-01-wif-sensor-kit-1.html>
- Racor RK-12870 LAK-1 kit: <https://www.amazon.com/Racor-12870-Water-Detection-Module/dp/B007I92B3K>
- Budget: $60–100. Phase 12.

### C.11 Engine runtime hours

No dedicated sensor. Three candidate inputs, cheapest first:

1. **Oil pressure switch → GPIO (via opto).** Runtime = integral of "oil pressure present." Works on any engine with a pressure switch (near-universal). Hours counted in HA template sensor. **Cost: $0 if the switch exists.**
2. **Alternator W terminal → optocoupler → GPIO pulse counter.** Gives runtime *and* RPM (pulses per revolution is fixed by alternator pulley). Needs a 4N35 and ~10 kΩ. **Cost: ~$2.**
3. Tach NMEA2000 bridge — overkill.

**Recommendation: start with oil-pressure switch (Phase 10); add W-terminal pulse counting if RPM becomes interesting.**

---

## D. Actuators (newly-in-scope for v2)

**The crucial framing:** remote actuation on an unattended boat has to be treated as a life-safety problem. The human on shore pressing "turn on heater" in HA is assuming every layer between finger and element works — WiFi, MQTT, cloud, firmware, relay logic, electrical, mechanical. **Default to physical interlocks and fail-safe defaults. Heater is the one I will push back on most.**

### D.1 Bilge blower

**Low risk, high value.** Blower moves engine-room air to reduce gasoline fume accumulation (less relevant on diesel, but still useful post-fueling).

- **Recommended:** **mechanical SPDT relay board** (Sainsmart 4-ch 12 V relay module, $8) switched by GPIO. Mechanical over SSR because the blower is an inductive DC motor; SSRs for DC inductive loads are a compromise.
- Alternative with more marine pedigree: **Blue Sea 7713 ML-RBS** (500 A coil-latching) — overkill for a 5 A blower, but the right answer for a battery disconnect actuator.
- Drive via ULN2003A Darlington array to give 5 V→12 V relay coil isolation and flyback protection.
- $15 total (relay + ULN2003A + wiring).

### D.2 Cabin fan on/off

Same pattern as blower. **Sainsmart 4-ch relay, one channel per fan, fused at 5 A each.** $8 of the same module. Low risk; fail-safe is "off."

### D.3 Heater relay

**Stop and think.** Two sub-cases:

1. **Diesel forced-air heater (Espar/Webasto):** has its own combustion controller with temperature sensing, flame-out detection, and fuel-pump logic. A relay here switches the heater's *enable* input, not the glow plug directly. **Acceptable.** Still needs:
   - Thermal fuse in the heater enclosure (OEM has one).
   - ESP32 watchdog → heater off after 4 h max runtime without user ack.
   - HA automation: heater only on if cabin temp < 10 °C *and* boat is occupied (how do we know? GPS motion in last 48 h, or a manual "occupied" toggle).
2. **Resistive 120 V AC space heater:** **Do not automate.** No thermal protection on a typical plug-in heater is certified for unattended operation. Kelly will see "heater on, boat empty, shore power" as fine; reality is a fire risk if something on top of the heater is set on fire.

**Recommendation:** only automate the diesel/propane heater's *enable* line, behind:
- Physical SPDT toggle labeled "AUTO / OFF" in the nav station. **OFF always wins.**
- Firmware watchdog: must see heartbeat and an acknowledged "user wants heat" MQTT message within 10 min, or relay drops.
- HA must require two-factor: "Pete confirms" + "cabin T < 5 °C."

### D.4 Refrigerator power cycle (edge case)

Use-case: fridge controller locked up, power cycling it remotely avoids a weekend of spoiled food.

- **Recommended:** mechanical relay on fridge's 12 V feed. Normally closed (relay energized = fridge on) — **fail-safe on power loss is "fridge still runs."** Relay coil de-energizing on firmware crash would be the wrong default.
- Rate-limit in HA: no more than 1 cycle per 30 min; max 6 per day.

### D.5 Safety interlocks — mandatory

| Control | Purpose | Implementation |
|---|---|---|
| **Physical kill switch** | Master OFF for all actuators | DPDT toggle between ESP32 output bank and ULN2003A input; "AUTO / OFF-ALL" on nav panel |
| **Firmware watchdog** | Auto-drop actuators on MCU hang | ESPHome `watchdog` component, 60 s timeout; all relays set `restore_mode: ALWAYS_OFF` |
| **MQTT heartbeat interlock** | Drop actuators if no command stream | HA keepalive every 60 s; ESP32 local automation drops any "ON" actuator after 5 min of silence |
| **Rate limit** | Prevent runaway cycling | HA rate limiters per-actuator |
| **Fail-safe defaults** | Blower=off, fan=off, heater=off, fridge=on | Set in ESPHome `on_boot` |
| **Per-actuator fuse** | Local overcurrent | ATO in-line at the relay |
| **Status feedback** | Detect stuck relays | Current-sense each switched line via INA219 or second GPIO reading fused 12 V downstream |

**Absolute rules:**
- No AC actuator to any device without OEM thermal protection.
- No remote-on for a resistive element that can ignite something.
- Every actuator has a mechanical override.

---

## E. Power subsystem deep dive

### E.1 12V → USB-C → pass-through bank — validate or challenge

**Summary:** the pass-through bank approach is acceptable but **pass-through is the single most under-tested claim in the whole BOM.** Cheap power banks advertise pass-through but gate the output briefly during charge/discharge transitions (typical "glitch" 100–500 ms, which *will* reboot the ESP32-S3 despite the 1000 µF bulk cap in some cases).

**Three alternatives, ranked:**

1. **Small 12 V LiFePO4 (10 Ah) in parallel on the feed + a proper LiFePO4-friendly charger.** This is how every professional marine installation does UPS. See E.4.
2. **12 V→5 V buck directly to ESP32 VIN with supercapacitor bank on 5 V rail for ~30 s ride-through.** Cheap ($15), no Li chemistry issue, but doesn't meet NF-3 (12 h runtime).
3. Pass-through USB-C power bank (current design). Cheap ($60), fits the existing USB-C plug of the DevKitC-1, but requires bench-verification.

### E.2 Recommended specific power bank

Based on 2026 community reports:

| Bank | Capacity | Pass-through? | Low-current cutoff? | Verdict |
|---|---|---|---|---|
| **Voltaic V50** | 12.8 Ah / 47 Wh | **Yes — "Always On" mode, explicit** | No on USB-A, unclear on USB-C — use USB-A output for ESP32 via USB-A→C cable to dodge this | **Primary recommendation** |
| INIU P63-E1 (100 W / 25000 mAh) | 25 Ah / 92.5 Wh | Marketed as pass-through | Unknown, will auto-cut at ~25 mA per most reports | Higher capacity but less-verified pass-through for continuous IoT; only viable after bench test |
| Zendure SuperMini (10000) | 10 Ah / 37 Wh | No longer explicit pass-through in current revs | — | Skip |
| Anker PowerCore 313 / 325 / 337 | varies | **Generally disables output during charge** — many reports | — | Skip for UPS duty |

**Recommendation:** **Voltaic V50 + USB-A→USB-C cable** feeding the DevKitC-1. Use USB-A port so we get "Always On" no-cutoff. Input via USB-C from the 12→USB-C PD buck. $60. Bench-soak 72 h with instrumented power-cut cycles before install.

- Voltaic V50 (Voltaic): <https://voltaicsystems.com/V50/>
- Voltaic V50 (Amazon): <https://www.amazon.com/Voltaic-Systems-Always-External-Battery/dp/B00XZ7YU4M>

### E.3 Quiescent draw accounting

| Component | Idle (mA @ 5 V) | Active (mA @ 5 V) |
|---|---|---|
| ESP32-S3-DevKitC-1 (WiFi connected, BLE scanning) | 60 | 140 (TX bursts) |
| dAISy HAT | 40 | 40 |
| NEO-M9N (3D fix, active antenna) | — | 30 |
| INA226 + shunt | <1 | <1 |
| SHT40 + BMP390 + ADS1115 | 1 | 1 |
| 3× DS18B20 | 3 | 3 |
| Relay coils (fail-safe OFF) | 0 | 0 |
| **Totals** | **~105 mA @ 5V = 525 mW** | **~215 mA @ 5V = 1075 mW** |

At 12 V input (assume 85% buck efficiency + 90% bank round-trip if on battery):
- **Idle draw on 12V house bank: ~60 mA = 1.4 Ah/day.**
- **Active: ~125 mA = 3 Ah/day.**
- **Mixed realistic duty: ~2 Ah/day.**

On a 300+ Ah Hunter 41DS house bank this is <1%/day.

**Voltaic V50 47 Wh runtime at 1 W load → ~47 h.** At realistic 1.5 W → ~31 h. Comfortably exceeds NF-3's 12 h requirement.

### E.4 LiFePO4 alternative

A **12 V 10 Ah LiFePO4** battery (e.g., Dakota Lithium 12V 10Ah, ~$130; or generic cell+BMS for $60) in parallel on the 12 V supply *behind a Schottky-OR diode from shore-charged bus* gives:

| Metric | LiFePO4 path | USB-C power bank path |
|---|---|---|
| Capacity | 128 Wh (10 Ah × 12.8 V) vs 47 Wh V50 | 47 Wh |
| Runtime at 1.5 W | ~85 h | ~31 h |
| Chemistry | LiFePO4 — safer, 2000+ cycles, -20 to +60 °C | Li-ion pouch — ~500 cycles, risky at 60 °C marina summer |
| Cost | $70–130 | $60 |
| Installation | Requires Schottky-OR or ideal-diode circuit; needs 14.4 V absorption-capable charger | Plug-and-play USB-C |
| Serviceability | 11-year warranty (Dakota), user-replaceable | 2-year warranty, not replaceable |

**Pete — this is the decision point of the whole power subsystem.** My recommendation: **switch to LiFePO4 for v1.1.** It's only ~$30 more than the V50, lasts 4× longer, handles marina-summer heat, and matches how the rest of the boat is built. Circuit:

```
12V house bank ──┬── ATO 5A ──┬── SMCJ30A TVS ──┬── 12→USB-C buck ── ESP32-S3
                 │            │                 │
                 │            │                 └── (bank absorbs dip)
                 │            │
                 └── charger ─┴── LiFePO4 10Ah ── Schottky ── (rejoins 12V bus)
```

If we go LiFePO4, the only new parts are:
- Dakota Lithium 12V 10Ah or similar: $130
- Victron Blue Smart IP22 12/10 charger (from house bank via DC-DC, optional) OR direct from charged bus via Schottky: $0
- 2× Schottky 20 A (e.g., SBR20U300CT): $2
- Drop the Voltaic V50: −$60

**Net +$72 for 4× the runtime, safer chemistry, 11-year warranty.**

---

## F. Enclosure & mounting deep dive

| Enclosure | Material | IP | Interior (WxDxH) | $ | Fit |
|---|---|---|---|---|---|
| **Polycase WC-23F** | ABS | IP66 / NEMA 4X | 6.26×4.37×3.5" | $35 | Good — designed for clear-cover LED displays; we don't need clear but pricing includes flange mounts |
| Polycase WP-23F | Polycarbonate | IP65 | Similar | $37 | Slight UV advantage — useful if mounted in cockpit |
| Bud NBB-15242 | Fiberglass | IP66 | 9.9×7.7×3.9" | $45 | More room; fiberglass = less UV-brittle than ABS |
| Hammond 1554 (B/C) | Polycarbonate | IP66 | 4.7×4.7×2.2" | $25 | Compact but tight with dAISy HAT + buck + bank |
| Pelican Micro 1020 / 1040 | ABS | IP67 | Small | $20 | Cable entry hacked on — not designed for it |

**Recommendation: Polycase WC-23F** (keep v1.0 nomination). It's the sweet spot for fit, price, and cable-gland flexibility. Mount internally on a short TS-35 DIN rail; everything (ESP32 carrier, INA226, ADS1115, terminal blocks) gets DIN clips or double-sided-taped to the rail.

**Installation detail to add to §13:**
- Drill bulkhead entries *only* on the bottom or lower sides — never the top — even on an IP66 box.
- Cable glands: Heyco M3223 series in PG9/PG11 — strain-relieved and sealed.
- Desiccant pack inside (silica gel, 20 g).

**Conformal coating:** **MG Chemicals 422B** on the finished ESP32 carrier + dAISy breakout, masking off USB-C, button, antenna pin, and the dAISy VHF input. One coat, brushed. The silicone-acrylic blend is specifically marketed for marine/aerospace. ~$20 for a 55 mL pen.

- Polycase WC-23F: <https://www.polycase.com/wc-23f>
- MG 422B pen: <https://mgchemicals.com/products/conformal-coatings/silicone-conformal-coatings/silicone-modified-conformal-coating/>

---

## G. Connectors

| Option | Pros | Cons | Cost per circuit |
|---|---|---|---|
| **M12 A-coded 5-pin (v1.0 choice)** | Industry-standard IP67; cheap panel-mount parts on Digi-Key; dozens of pre-made cables | Threaded connector can back out under vibration if not torqued | $15–20 (panel + mate) |
| Turck / Binder industrial | Better seal quality, hex-nut grip | 2× price for no marine-specific advantage | $30–40 |
| **Deutsch DT04-series** | Marine/automotive gold standard; positive latch; Kevin-proof | Crimp tooling is $200+; panel-mount kits rarer | $10–15 + tooling |
| Marinco / SeaLink circular | Dedicated marine | Very expensive; overkill | $40+ |

**Recommendation:** **M12 A-coded for signal (sensors, opto outputs, dry contacts), Deutsch DT for high-current actuator outputs.** Why split:
- M12 is fine for sub-amp signal wiring and has huge cable ecosystem.
- Deutsch DT is the right home for blower / fan / heater-enable / fridge-relay outputs — it's the connector every marine mechanic already knows how to service with a $30 crimper (TE 0411-336-1605 or Harbor Freight knockoff).

Panel seal rule: all bulkhead connectors torqued to spec with panel gasket; silicone grease on O-rings; never rely on raw thread seal alone.

---

## H. Validated BOM with total cost

> **v2 SIMPLIFIED BOM (current, April 23 2026) — see [`simplicity-review.md §4`](simplicity-review.md) for authoritative Phase 1–6 parts list.** The tables below preserved as v1.1 historical reference + still-authoritative Phase 7–11 details.

### H.1 (v2) Phase 1–6 — Summary (authoritative list: simplicity-review §4)

Feather + STEMMA QT ecosystem replaces DevKitC-1 + hand-wired breakouts. USB-C input jack replaces 12V power chain (external marine USB-C outlet). Shelly Plus Plug S replaces in-enclosure opto-isolators.

| Category | Items | Approx $ |
|---|---|---|
| Core compute (Feather + proto + dAISy) | 3 | $98 |
| Sensors (Qwiic INA228, BME280, 3× DS18B20 lead, float) | 6 | $75 |
| AC detection (2× Shelly Plus Plug S) | 2 | $40 |
| Tier 0 alarm (LED + buzzer module) | 2 | $4 |
| Enclosure (Feather IoT box + panel jacks) | 3 | $24 |
| Power (Scanstrut ROKK Charge+ external) | 1 | $65 |
| Consumables (wire, ferrules, heatshrink, glands) | kit | $20 |
| Cables (STEMMA QT kit, USB-C) | kit | $15 |
| Pullup resistor | 1 | $0.10 |
| **Phase 1–6 total** | | **≈$341** |

Plus infrastructure (HA Green $99, Pi 4 + SSD $95) = **$535 to v1 ship**.

### H.1-legacy (v1.1 historical, superseded by simplicity review)

<details>
<summary>Click to expand v1.1 Phase 1–6 BOM (DevKitC-1 + hand-wired, replaced)</summary>

**Core compute (Phase 1–4):** DevKitC-1 $17 · CZH-Labs breakout $20 · dAISy $75 · Polycase WC-23F $35 · DIN rail + clips $9 · PG9/11 glands $9 · 4× M12-A bulkheads + mates $92 · 2× Deutsch DT $24 · marine wire + ferrule kit + heatshrink + conformal $150. **Subtotal: $431**.

**Power (Path A — USB-C bank):** 12V→USB-C PD buck $25 · Voltaic V50 bank $60 · USB-C cables $16 · fuse/TVS/cap $16. **$117.**
**Power (Path B — LiFePO4):** Dakota 10Ah $130 · Pololu buck $20 · OR diodes $2 · fuse/TVS/cap $16. **$168.**

**Sensors (Phase 5/6):** 3× DS18B20 $24 · SHT40 $10 · BMP390 $10 · INA226 + shunt $20 · V-divider $1 · 2× HiLetgo 120VAC opto $16 · float switch $28. **$109.**
</details>

### H.4 Sensors — Phase 7–10 (stretch/full)

| Item | Part | Source | Qty | Unit $ | Ext $ |
|---|---|---|---|---|---|
| Victron SmartShunt 500A IP65 | SHU065150050 | Powerwerx | 1 | 111 | 111 |
| u-blox NEO-M9N breakout | SparkFun GPS-15210 | SparkFun | 1 | 75 | 75 |
| Active GPS antenna 28 dB, SMA | Taoglas or generic | Digi-Key | 1 | 15 | 15 |
| Adafruit ADS1115 16-bit ADC | 1085 | Adafruit | 1 | 15 | 15 |
| DS18B20 additional (for full 10-zone) | Adafruit 381 | Adafruit | 6 | 8 | 48 |
| TCA9548A I²C mux (for SHT40 fleet) | Adafruit 2717 | Adafruit | 1 | 7 | 7 |
| Additional SHT40 sensors | 4885 | Adafruit | 2 | 10 | 20 |
| JSN-SR04T-V3.0 ultrasonic | — | Amazon | 1 | 10 | 10 |
| Fireboy-Xintex CMD-5M CO alarm | CMD-5M | Defender | 1 | 90 | 90 |
| Racor WIF kit (probe + LAK-1) | RK23191-01 + RK12870 | Defender / Amazon | 1 | 80 | 80 |
| 4N35 optocoupler (oil-pressure switch, W-term) | Digi-Key | Digi-Key | 2 | 1 | 2 |
| **Phase 7–10 subtotal** | | | | | **$473** |

### H.5 Actuator package (Phase 11 / v2)

| Item | Part | Source | Qty | Unit $ | Ext $ |
|---|---|---|---|---|---|
| 4-ch 12 V relay module (mechanical) | Sainsmart 4-ch | Amazon | 1 | 9 | 9 |
| ULN2003A Darlington array | Texas Instruments | Digi-Key | 2 | 1 | 2 |
| Flyback diodes (1N4007) | Digi-Key | Digi-Key | 10 | 0.10 | 1 |
| Panel DPDT kill switch ("AUTO/OFF-ALL") | C&K 7101 | Digi-Key | 1 | 5 | 5 |
| Panel SPDT "OFF wins" toggle for heater | C&K 7101 | Digi-Key | 1 | 5 | 5 |
| Blue Sea 7713 ML-RBS (if battery-disconnect actuator desired) | 7713 | Defender | 1 (opt) | 130 | 130 |
| INA219 breakout for relay downstream current sense | Adafruit 904 | Adafruit | 4 | 10 | 40 |
| Deutsch DT 4-pin connectors for actuator outputs | DT04-4P | New Wire Marine | 4 | 12 | 48 |
| **Actuator package subtotal (excluding 7713)** | | | | | **$110** |
| **Actuator package subtotal (including 7713)** | | | | | **$240** |

### H.6 Cloud

| Item | Cost |
|---|---|
| Oracle Cloud Always Free (2× ARM A1.Flex) | $0 |
| Domain + Let's Encrypt | $0 |
| Mosquitto + WireGuard + Python | $0 |

### H.7 (v2) Grand totals — simplified

| Scope | $ |
|---|---|
| Phase 1–6 (core + sensors + AC detect + enclosure + USB-C power + consumables) | $341 |
| Infrastructure (HA Green $99 + Pi 4 + SSD $95) | $194 |
| **v1 ship gate (Phase 6) TOTAL** | **$535** |
| Phase 7 (Victron BLE — $0 firmware; SmartShunt if not installed: +$111) | 0–$111 |
| Phase 8 (Adafruit Ultimate GPS FeatherWing $40 + active antenna $15 + ADS1115 Qwiic $15) | $70 |
| Phase 9 (software only) | $0 |
| Phase 10 (7 more DS18B20 $56 + optional RJ12 hub $35) | $56–$91 |
| **Phase 1–10 full build** | **$661–$807** |
| Actuator package (Phase 11, no 7713) | +$110 |
| Optional: Anker 733 UPS | +$110 |

**Net simplicity delta:** compared to the v1.1 path-B estimate ($1,291 full), the simplified design drops to **~$807 full build** — a **$484 reduction**, driven by:
- Externalized power ($168 → $65 Scanstrut outside the enclosure)
- No discrete M12 bulkhead assemblies ($116 saved)
- No Deutsch DT for actuator outputs (deferred)
- No Polycase + DIN rail + conformal coating
- Feather ecosystem eliminates breakout-bundle cost
- Shelly plugs replace custom AC-opto boards
- Single-weekend hand-soldering eliminated (time-value)

---

## I. Availability check (April 2026)

| Part | Digi-Key | Mouser | Amazon | Adafruit/SparkFun | Notes |
|---|---|---|---|---|---|
| ESP32-S3-DevKitC-1-N16R8V | Stock | Stock | Stock | Stock (Adafruit) | Plenty everywhere |
| dAISy HAT | — | — | — | shop.wegmatt.com only | Single-source, hand-assembled in WA. Buy 2 if worried |
| Polycase WC-23F | — | — | — | polycase.com only | Polycase direct ships 1–3 days |
| Voltaic V50 | — | — | Stock | voltaicsystems.com | Direct is most reliable |
| Dakota Lithium 12V 10Ah | — | — | Stock | dakotalithium.com | Stocked |
| Victron SmartShunt IP65 500A | — | — | Stock | Defender / Powerwerx | Stocked |
| NEO-M9N / SparkFun GPS-15210 | Stock | Stock | — | SparkFun | Stocked (SparkFun made), but watch for lead spikes on u-blox modules broadly |
| ADS1115 | Stock | Stock | Stock | Adafruit (1085) | Abundant |
| INA226 / INA228 | Stock (ICs) | Stock | Stock (breakouts) | — | Abundant |
| SHT40 / BMP390 | Stock (Sensirion/Bosch) | Stock | Stock | Adafruit | Abundant |
| Fireboy-Xintex CMD-5M | — | — | Stock | Defender | Marine chandlery |
| Racor RK23191-01 / RK12870 | — | — | Stock | Defender / racorstore.com | Stocked |
| Rule-A-Matic Plus | — | — | Stock | Defender | Stocked |
| Blue Sea 7713 | — | — | Stock | Defender | Stocked |
| Deutsch DT connectors | Stock | Stock | Stock | New Wire Marine (marine kits) | Abundant |

**Nothing flagged at >8 week lead time.** Known single-source items: dAISy HAT (one shop), Polycase (one vendor), Voltaic (one vendor). For each, consider ordering 1 spare up front — the differential cost is trivial against a rebuild-delay.

---

## J. Open questions for Pete

These are the decisions that should land before BOM is locked:

1. **Power subsystem Path A vs B?** My recommendation is Path B (LiFePO4) for reliability and thermal margin. +$51. Your call — does "one more marine battery on the boat" feel like less ops risk to you than "one more sealed gadget with a cell inside"?
2. **Victron SmartShunt timing.** If the electrical upgrade installs one anyway, skip INA226 on the house bank. If it lands after v1 ships, INA226 is the bridge. Which way is the upgrade sequencing?
3. **How much actuator scope in v1?** The actuator package is in-scope per your ask, but everything other than the bilge blower really wants Phase 2+ thinking (interlocks, physical switches, cable runs). Are we shipping actuators in v1, or in a clearly-labeled v1.5?
4. **Heater scope.** Do you want me to design for "remote-enable diesel heater behind interlocks" or leave heater entirely out? I will refuse to wire an unprotected AC space heater for remote actuation.
5. **Connector philosophy.** M12 everywhere, or M12-for-signal + Deutsch-for-actuator as I've proposed? The hybrid adds ~$50 and one crimper.
6. **Spare counts.** Buy 2× dAISy HAT, 2× WC-23F, 2× DevKitC-1 up front for bench + boat + spare? Adds ~$130 total.
7. **CO alarm.** Is a Fireboy-Xintex already installed on the Hunter 41DS? If so, we just wire its dry-contact output; if not, it's $90 new and solves a non-EvenKeel safety problem that happens to be cheap to ingest.
8. **Tank sender protocol.** v1.0 notes US 240–33 Ω. Verify at survey. If it's 10–180 Ω European, the ADS1115 lookup tables change.
9. **Engine oil-pressure-switch polarity.** Most Yanmar/Volvo/Westerbeke switches close to ground with low oil pressure (i.e., "inverted"). Confirm on the Hunter's engine at survey so we get the "running" logic right on first try.
10. **UPS bench-test plan.** Regardless of Path A/B, spec a 72 h bench soak with scripted power-cut events every 10 min for the first hour, then every 30 min for the remainder. Budget: one weekend on Pete's bench.

---

## Sources

- [ESP32-S3-DEVKITC-1-N32R8V product page, Digi-Key](https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-DEVKITC-1-N32R8V/15970965)
- [Espressif DevKits](https://www.espressif.com/en/products/devkits)
- [ESPHome OpenThread (C6/H2) docs](https://esphome.io/components/openthread/)
- [ESPHome 2026.3.0 release notes — RP2350 verification](https://esphome.io/changelog/2026.3.0/)
- [Wegmatt dAISy HAT](https://shop.wegmatt.com/products/daisy-hat-ais-receiver)
- [Wegmatt dAISy 2+](https://shop.wegmatt.com/products/daisy-2-dual-channel-ais-receiver-with-nmea-0183)
- [Quark-Elec QK-A026](https://www.quark-elec.com/product/a026-wireless-ais-gps-receiver/)
- [NASA AIS Engine 3](https://www.nasamarine.com/product/ais-engine-3/)
- [ESPHome INA2xx docs](https://esphome.io/components/sensor/ina2xx/)
- [ESPHome INA226 docs](https://esphome.io/components/sensor/ina226/)
- [latonita/esphome-ina228 external component](https://github.com/latonita/esphome-ina228)
- [ESPHome SHT4x docs](https://esphome.io/components/sensor/sht4x/)
- [Adafruit SHT40 (4885)](https://www.adafruit.com/product/4885)
- [Adafruit BMP390 (4816)](https://www.adafruit.com/product/4816)
- [Adafruit DS18B20 waterproof (381)](https://www.adafruit.com/product/381)
- [Adafruit ADS1115 (1085)](https://www.adafruit.com/product/1085)
- [Adafruit TCA9548A (2717)](https://www.adafruit.com/product/2717)
- [ESPHome JSN-SR04T docs](https://esphome.io/components/sensor/jsn_sr04t/)
- [SparkFun GPS-15210 NEO-M9N](https://www.sparkfun.com/products/15210)
- [hugokernel/esphome-zmpt101b](https://github.com/hugokernel/esphome-zmpt101b)
- [ESPHome MH-Z19 docs](https://esphome.io/components/sensor/mhz19/)
- [Victron SmartShunt product](https://www.victronenergy.com/battery-monitors/smart-battery-shunt)
- [Powerwerx SmartShunt 500A IP65 listing](https://powerwerx.com/victron-shu065150050-smartshunt-ip65-500a)
- [Polycase WC-23F](https://www.polycase.com/wc-23f)
- [MG Chemicals 422B silicone conformal coating](https://mgchemicals.com/products/conformal-coatings/silicone-conformal-coatings/silicone-modified-conformal-coating/)
- [Voltaic V50 product page](https://voltaicsystems.com/V50/)
- [Voltaic V50 on Amazon](https://www.amazon.com/Voltaic-Systems-Always-External-Battery/dp/B00XZ7YU4M)
- [INIU P63-E1 product page](https://iniushop.com/products/iniu-p63-e1-power-bank-smallest-100w-25000mah)
- [Dakota Lithium 12V 10Ah Power Box](https://www.amazon.com/Dakota-Lithium-Power-Charger-Black/dp/B07HS3FYKB)
- [Racor RK23191-01 WIF probe](https://www.racorstore.com/racor-rk23191-01-wif-sensor-kit-1.html)
- [Racor RK-12870 LAK-1 alarm kit](https://www.amazon.com/Racor-12870-Water-Detection-Module/dp/B007I92B3K)
- [Blue Sea 7713 ML-RBS](https://www.bluesea.com/products/7713/ML-RBS_Remote_Battery_Switch_with_Manual_Control_Auto-Release_-_12V)
- [New Wire Marine Deutsch-compatible connector guide](https://newwiremarine.com/deutsch-compatible-connectors/)
- [Amphenol M12 A-coded guide](https://amphenolltw.com/news-events/m12-connector-types-coding.html)

*End of hardware deep dive v1.1.*
