# EvenKeel — Simplicity Review

**Mandate:** Rework the hardware BOM so EvenKeel is genuinely DIY-possible. No PCB etching, no fussy wiring of discrete parts, no AC voltage entering the boat-node enclosure. Plug-together wherever possible.

**Headline:** by swapping to the **Adafruit Feather + STEMMA QT (Qwiic) ecosystem** and moving AC detection + power conditioning **out of the enclosure**, we cut the boat-node from ~30 discrete parts + extensive soldering down to **~7 plug-together modules and a terminal block**. v1 build time drops from an estimated full weekend to a few hours.

---

## 1. Guiding Principles (new)

1. **Plug, don't solder.** Every I²C sensor connects via a 4-pin JST-SH (Qwiic/STEMMA QT) cable. Zero exposed wire. Zero solder joints for sensors.
2. **Commodity externally, ESPHome internally.** Use certified consumer products (Shelly, Scanstrut, Anker) to handle anything AC-voltage or surge-prone. The enclosure has only low-voltage signals and a USB-C input.
3. **USB-C is the only power interface.** The boat-node enclosure has one USB-C receptacle. How it gets 5V is the user's choice: automotive adapter, power bank, wall brick.
4. **Pre-assembled wherever possible.** Float switch with leads, DS18B20 with 3 m waterproof lead, Shelly smart plug already in a UL-listed housing — use these instead of re-inventing.
5. **3D-printable or off-the-shelf enclosure with templated cutouts.** No custom drilling of Polycase boxes.
6. **If a breakout board exists on Adafruit / SparkFun / Pimoroni with a Qwiic connector, use it.** Avoid generic Amazon/Aliexpress modules that need manual wiring.

---

## 2. Current-Design Complexity Audit

The `hardware-deep-dive.md` BOM as locked has these DIY friction points:

| Friction | Why it hurts |
|---|---|
| ESP32-S3 DevKitC-1 + separate screw-terminal breakout + dAISy HAT | Three PCBs to mechanically mate; no standard interconnect |
| 12V→USB-C buck + TVS + fuse holder + 1000µF cap + reverse-polarity MOSFET | 5 discrete parts on a perfboard or DIN terminal. AC-adjacent wiring. |
| Discrete INA226 + ADS1115 + BME280 I²C modules, hand-wired | ~12 solder joints, 4-wire I²C chain with no standard connector |
| 2× 120V opto-isolator modules in the enclosure | AC voltage enters the boat-node enclosure. Requires code compliance, fusing, insulation. |
| Polycase WC-23F drilled for 4–6 M12 bulkheads | Cost of a step drill + template; 30-60 min per hole |
| DS18B20 probes with loose leads landed on terminal blocks | No strain relief, no bus topology discipline |
| LED + piezo on Tier 0 cable, hand-crimped M12 | Another custom cable assembly |

Count of solder joints in the original plan: **~50–60.** Build time estimate: **a full weekend plus 72 h soak.**

---

## 3. Proposed Simplifications (with part numbers)

### 3.1 Core compute — swap to **Adafruit ESP32-S3 Feather**

**Before:** ESP32-S3-DevKitC-1 + CZH-Labs screw-terminal breakout board.

**After:** **Adafruit ESP32-S3 Feather** (8MB flash / 2MB PSRAM variant, part #5477, ~$18).

Why:
- Has a **STEMMA QT connector built in** (daisy-chain I²C sensors with no solder).
- USB-C power/programming on board.
- Integrated LiPo charger if Pete ever wants to add battery backup — optional.
- Feather "doubler" / "tripler" boards from Adafruit exist if we need a second board (e.g., a custom breakout for the dAISy UART + float switch + Tier 0 GPIO) — one solder session, done forever.
- ESPHome first-class support for `board: adafruit_feather_esp32s3`.

Alternative considered: **Unexpected Maker FeatherS3** (~$22) — same form factor, 8MB PSRAM. Pick based on stock.

**One-time soldering:** solder a **Featherwing proto board** (Adafruit #2884, $4.95) with screw terminals for dAISy 3-wire, bilge float 2-wire, Tier 0 LED+buzzer 3-wire. One evening. After that, everything else is plug-in.

### 3.2 Power — ONE USB-C receptacle. That's it.

**Before:** 12 V house bank → ATO fuse → TVS diode → bulk cap → reverse-polarity MOSFET → 12V-to-USB-C PD buck → USB-C cable → Feather.

**After:** USB-C cable → Feather. **Nothing else in the enclosure.**

Everything upstream of USB-C is the user's choice, and it's now a commodity purchase:

| Option | Part | Price | Notes |
|---|---|---|---|
| **A. Marine USB-C outlet** | Scanstrut ROKK Charge+ USB-C (SC-USB-04) | ~$65 | IP66, 12/24V input, PD 60W, reverse-polarity + over-current built in. Wire once, forget. |
| **B. Automotive USB-C** | Anker PowerDrive III Duo 48W (A2725) | ~$20 | Plugs into a 12V cigarette socket or hard-wire with a $3 pigtail. Also reverse-polarity protected. |
| **C. Power bank UPS** | Anker 733 GaNPrime PowerCore 10K | ~$110 | Pass-through, gives ~20h runtime if boat 12V dies. Optional. |
| **D. Wall brick at dock** | Any USB-C PD 20W+ brick | ~$15 | For bench / marina-shore-power-only setups. |

The only thing we enforce: **the USB-C source must deliver at least 5 V / 2 A**. A Feather ESP32-S3 idles ~100 mA; with dAISy (100 mA) + sensors (50 mA) peaks at ~400 mA. 10 W PD is more than enough.

**What we give up:** no true in-enclosure TVS for lightning/engine-transient surges. The marine-rated Scanstrut unit has surge suppression to ISO 7637-2 Level 4 internally, which covers engine-start transients. For lightning, nothing at this price class survives a direct strike anyway — that's a re-buy scenario.

**Bill of materials removed:** fuse holder + fuse, TVS, bulk cap, MOSFET, DIN-rail buck, wiring harness. **~$50 and 5-6 parts eliminated.**

### 3.3 Sensors — Qwiic/STEMMA QT ecosystem only

**Before:** generic Amazon I²C breakouts, hand-wired.

**After:** every I²C sensor has a JST-SH connector. Daisy-chain with 50/100/200mm STEMMA QT cables ($0.95–$1.95 each).

| Sensor | Part | Price | Phase |
|---|---|---|---|
| **Current/voltage (house bank)** | Adafruit INA228 Qwiic (#5832) | $14.95 | 5 |
| **Cabin T/RH/pressure** | Adafruit BME280 STEMMA QT (#2652) | $14.95 | 5 |
| **Tank ADC (4 channels)** | Adafruit ADS1115 STEMMA QT (#1085 revised) | $14.95 | 8 |
| **Additional humidity/temp** | Adafruit SHT40 STEMMA QT (#4885) | $4.95 | 5+ |

Everything chains off the Feather's STEMMA QT port. No hand-wired I²C. **Zero soldering for these sensors.**

Three cables of different lengths come in a kit (Adafruit #4210, $5.95). Plan on one per sensor.

### 3.4 1-Wire temperature — pre-assembled waterproof probes + RJ12 hub

**Before:** loose DS18B20 probes on terminal blocks, no hub, no pullup board.

**After:** two options, both plug-together.

#### Option 1 — Hobby-Boards "1-Wire RJ12" ecosystem (recommended)

Open-standard 1-Wire over RJ12 is common in the home-automation world. Pete builds the "hub" on the Featherwing proto board: one RJ12 jack + 4.7 kΩ pullup. Then:

- **Hobby-Boards 6" RJ12 daisy-chain** splitters (8-port hub ~$35) — lets you run one bus cable to a hub, then branch to 8 sensor probes via RJ12.
- **Prewired DS18B20 probes** in RJ12 connectors: DIY by crimping a $0.20 RJ12 onto a $10 Adafruit #381 waterproof probe (5 min per probe), OR buy ready-made from iButtonLink ($15-20 each).

#### Option 2 — simpler, fewer probes (recommended for Phase 5's 3 probes)

Just use **three Adafruit #381 waterproof DS18B20s** (3m lead, already jacketed, $10 each). Land the three leads on the Featherwing proto with a single 4.7 kΩ pullup to 3.3V. No hub, no RJ12. Add more probes later only when we actually add zones in Phase 10 — at that point, adopt Option 1.

**Recommendation:** start with Option 2 for v1. Upgrade to Option 1 only if Phase 10 happens.

### 3.5 AC detection — replace in-enclosure opto-isolators with **Shelly Plus Plug S**

**Before:** 2× generic 120V opto-isolator modules wired into the boat-node enclosure via M12 J3. AC voltage inside the enclosure. Code-questionable.

**After:** **Shelly Plus Plug S** (~$20 each on shelly.com or Amazon), UL-listed smart plug that measures AC voltage, current, power, and energy.

- Plug one between shore-power receptacle and shore-power cable: reports shore presence.
- Plug one between generator outlet and whatever you plug into it (an always-on draw like a dehumidifier if any, OR wire the generator output leg through a Shelly 1PM): reports genset presence.
- Both publish via **Shelly's native MQTT** (one checkbox in the UI) or via the Shelly integration in HA.

Benefits:
- **No AC in the boat-node enclosure.** Certified, listed device handles isolation.
- Gets you power consumption as a bonus (watts, amps, kWh of shore use).
- Removes 2 opto modules + M12 connector J3 + wiring from the BOM.

**Alternative if user doesn't want 2 Shelly plugs in-line:** keep a single opto-iso for shore-AC only (cheapest detection) and drop generator detection to "rising current on the SmartShunt" inference. Reduces to 1 opto.

### 3.6 Bilge float — pre-wired, direct to terminal

**Before:** Rule-A-Matic Plus → M12 J3 → inside enclosure → GPIO.

**After:** same switch, but lands directly on the Featherwing proto screw terminal. Use a **waterproof 2-pin marine connector** on the cable at the enclosure wall (or just a grommet — float switch leads are already marine-rated). No M12 needed.

Savings: one M12 bulkhead ($15) eliminated.

### 3.7 Tier 0 alarm — **M5Stack ATOM Echo / ATOM Lite** as a dedicated satellite

**Before:** discrete LED + piezo buzzer, wired off GPIO of the main ESP32, routed through M12 J6 to helm.

**After:** a tiny dedicated ESP32 satellite — **M5Stack ATOM Lite** (~$12) or **M5Stack ATOM Echo** (~$15, has a speaker).

- Runs a 20-line ESPHome YAML. Subscribes to `boat/hunter41/alarms/tier0` MQTT (or listens via native API from BoatMon-1).
- Drives an LED (ATOM Lite has one built-in) and a buzzer (ATOM Echo has a speaker that can play an actual siren wav).
- Fed from a USB-C micro adapter anywhere convenient — no cable run from the main box.

**Downside:** this is no longer GPIO-direct from the monitoring firmware — there's an MQTT hop in between. Re-evaluate:

**Compromise:** keep a minimal GPIO-direct LED+buzzer on the main enclosure face (a $3 pre-assembled active-buzzer module driven off a GPIO), AND also run an ATOM Echo at the helm for spoken alarms and extra volume. Belt-and-suspenders.

For v1 simplicity, ship only the in-enclosure LED+buzzer. Add the ATOM Echo only if a helm repeater is desired.

### 3.8 Enclosure — 3D-printable panel OR Waveshare IoT box

Two paths, both simpler than drilling a Polycase.

#### Path A — Waveshare "UPS HAT" style IoT box (off-the-shelf, no 3D printer)

- **Waveshare PLA enclosure for Adafruit Feather** form factor — several vendors make these on Amazon for $10-15.
- Cover plate with pre-cut USB-C opening + a panel-mount BNC jack ($3 from Digi-Key) for the AIS antenna.
- Keep everything else (Qwiic sensors, 1-Wire) as pigtails exiting via a single cable gland.

#### Path B — 3D-printed face plate (if Pete has a printer or wants a friend to print)

- Design in OpenSCAD or Fusion 360; publish STL alongside the repo.
- Pop-out openings for: 1× USB-C panel mount, 1× BNC antenna, 1× Qwiic pass-through (via JST-SH panel connector — SparkFun sells these), 1× RJ12 for 1-Wire (if we adopt Option 1), 1× 2-pin marine connector for bilge float, 1× 3-pin for Tier 0 if external.
- Print in **PETG or ASA** (UV-stable, marine-tolerant). Avoid PLA (deforms at 55 °C; a sun-baked cabin exceeds that).
- Model reference: we'll fork an existing marine-instrument panel design from Printables rather than draw from scratch. Targets: search "DIN instrument hole 62 mm" or "B&G Triton cutout".

**Recommendation:** start with Path A (a Feather-sized off-the-shelf IoT box) for Phase 3. Consider Path B for a polished final install in Phase 10+.

#### IP rating truth
Neither Path A nor Path B is genuinely IP66 without design effort. For EvenKeel's install target (nav station / dry locker), IP44 "splash-resistant" is sufficient. If Pete ever mounts exposed to cockpit weather, revisit with a Hammond 1554WDTCL or similar proper IP66 PLA-injection box.

### 3.9 dAISy — keep, just mount cleanly

dAISy HAT is already a finished product. We don't need to change it. Three-wire connection to Feather is four solder joints on the Featherwing proto (TX, GND, 3.3 V). Mount dAISy to the inside of the enclosure with stick-on standoffs (Keystone 8822-style) — no screws required.

---

## 4. Simplified BOM (v1 Phase 1–6)

Replacing the Phase 1–6 section of `hardware-deep-dive.md`:

| # | Item | Part / Source | Qty | Unit $ | Ext $ |
|---|---|---|---|---|---|
| 1 | ESP32-S3 Feather | Adafruit #5477 | 1 | 17.50 | 17.50 |
| 2 | Featherwing proto board (for dAISy UART + float + Tier 0 GPIO) | Adafruit #2884 | 1 | 4.95 | 4.95 |
| 3 | dAISy HAT | Wegmatt shop | 1 | 75.00 | 75.00 |
| 4 | STEMMA QT cable kit (50/100/200mm) | Adafruit #4210 | 1 | 5.95 | 5.95 |
| 5 | INA228 Qwiic (house V/I) + 100A shunt | Adafruit #5832 + shunt | 1 | 25.00 | 25.00 |
| 6 | BME280 STEMMA QT (cabin T/RH/baro) | Adafruit #2652 | 1 | 14.95 | 14.95 |
| 7 | Waterproof DS18B20 w/ 3m lead | Adafruit #381 | 3 | 10.00 | 30.00 |
| 8 | Rule-A-Matic Plus float switch | Defender | 1 | 25.00 | 25.00 |
| 9 | Shelly Plus Plug S (shore + gen detect) | shelly.com | 2 | 20.00 | 40.00 |
| 10 | Pre-assembled 3.3 V active buzzer module (Tier 0) | Amazon generic | 1 | 3.00 | 3.00 |
| 11 | 5 mm red LED + 330Ω resistor (Tier 0) | Adafruit | 1 | 1.00 | 1.00 |
| 12 | Feather-sized IoT enclosure (PLA/ABS off-the-shelf) | Amazon | 1 | 15.00 | 15.00 |
| 13 | BNC panel-mount for dAISy antenna | Digi-Key | 1 | 4.00 | 4.00 |
| 14 | USB-C panel-mount jack + pigtail | Adafruit #4218 | 1 | 5.00 | 5.00 |
| 15 | Scanstrut ROKK Charge+ USB-C (marine 12V→USB-C) | Scanstrut | 1 | 65.00 | 65.00 |
| 16 | 4.7 kΩ resistor (1-Wire pullup) | — | 1 | 0.10 | 0.10 |
| 17 | Tinned marine wire, ferrules, heatshrink | (consumables) | — | 15.00 | 15.00 |
| 18 | Cable glands, small grommets | — | — | 5.00 | 5.00 |
| | **Phase 1–6 SUBTOTAL** | | | | **$350.45** |

Plus one-time infrastructure (unchanged):
- Home Assistant Green: $99
- Raspberry Pi 4 4GB + 128GB USB SSD: $95
- **Infra subtotal: $194**

**v1 total: ~$544.** Compared to the ~$524 of the prior simplified design, we **haven't spent more money — we just spent it differently.** We gave up an in-enclosure TVS/fuse/buck in favor of a marine-grade external USB-C outlet; we gave up in-enclosure AC optos in favor of UL-listed smart plugs.

**Solder joints: ~15** (Featherwing proto for dAISy + float + Tier 0). Every sensor after that is plug-in. **Build time: ~3 hours instead of a weekend.**

---

## 5. Where Each Simplification Lives

| Phase | What changes |
|---|---|
| Phase 0 | Unchanged |
| Phase 1 | Same Feather + dAISy; now with STEMMA QT port available for future sensors |
| Phase 2 | Unchanged |
| Phase 3 | **Major change.** See §3.1–§3.8 above. Drops from "full weekend + soak" to "an evening + soak". Eliminates AC wiring, fuse, buck, most soldering. |
| Phase 4 | Same install concept; the enclosure is smaller and the power side is a separate commodity purchase |
| Phase 5 | Sensors are Qwiic; Shelly Plus Plug S handles AC; DS18B20 pre-assembled |
| Phase 6 | Automations unchanged |
| Phase 7 | Victron BLE — ESP32-S3 Feather still has BLE built-in, no change |
| Phase 8 | GPS — Adafruit Ultimate GPS FeatherWing ($40) stacks on top of Feather. No UART wiring to do. Tanks via Qwiic ADS1115. |
| Phase 9 | Unchanged (software) |
| Phase 10 | Additional DS18B20 probes: adopt 1-Wire RJ12 hub (§3.4 Option 1) if probe count >4 |

**Phase 8 bonus:** Adafruit Ultimate GPS FeatherWing is a literal drop-in — stacks on the Feather, no UART wiring. **Phase 8 drops a weekend too.**

---

## 6. Trade-offs — What We Give Up

Be honest about these.

| Lost | Gained | Is it worth it? |
|---|---|---|
| In-enclosure TVS protection | Scanstrut's built-in ISO 7637-2 protection | Yes — Scanstrut is designed exactly for this |
| Custom-drilled Polycase "real marine" look | Plastic Feather IoT box | For v1, yes. Upgrade in Phase 10 if Pete wants aesthetics. |
| Direct AC sense wiring | Two certified smart plugs + 2× MQTT topics | Yes — far safer, gets watts/amps as bonus |
| Centralized wiring in one box | Shelly plugs in-line with shore + gen cables, DS18B20 probes running to the Feather | Trivial cabling delta |
| Adafruit is a single supplier | 2-3 week risk if Adafruit discontinues a Feather variant | Mitigated by buying 1 spare Feather |
| 1-Wire RJ12 hub "does Phase 10 at scale" | Deferred until Phase 10 actually happens | Pure win |

---

## 7. Pre-wired / DIY-Kit Checklist

What Pete should literally buy pre-assembled, no exceptions:

- ✅ **DS18B20 probes** (Adafruit #381 waterproof with 3 m lead)
- ✅ **Bilge float switch** (Rule-A-Matic Plus comes with leads)
- ✅ **dAISy HAT** (fully assembled, tested)
- ✅ **Every I²C sensor** (Qwiic breakouts with JST-SH)
- ✅ **Shelly Plus Plug S** (UL-listed smart plug, no wiring)
- ✅ **Scanstrut ROKK Charge+** (finished marine product)
- ✅ **USB-C cables** (Anker or equivalent, don't roll your own)
- ✅ **Tier 0 buzzer** (active buzzer module with 3-wire lead, $3)
- ✅ **Feather IoT enclosure** (off-the-shelf from Amazon)
- ✅ **BNC + USB-C panel-mount jacks** (already pre-assembled pigtails)

What's left to solder (one evening, with a basic iron):

- Featherwing proto board: 3 wires to dAISy, 2 wires to float, 3 wires to Tier 0 LED/buzzer, 1 pullup resistor for 1-Wire, 3 wires to the 3 DS18B20 leads.
- **About 15 joints total.** None of them are tiny SMD. Through-hole headers and screw terminals throughout.

---

## 8. 3D-Printable Files (future contribution)

If we go Path B (§3.8), the repo will include under `hardware/3d/`:

- `face-plate.stl` — bulkhead cover with cutouts
- `face-plate.f3d` — Fusion 360 source
- `panel-dimensions.md` — precise hole placement with tolerances
- `bom-3d.md` — M3 heat-set inserts, screws, gaskets

Printable on any consumer FDM printer (Prusa, Bambu, Ender). Material: PETG or ASA. Estimated print time: 2–3 hours.

This is an optional Phase 10 deliverable, not Phase 3.

---

## 9. Recommended Decisions

| # | Decision | My rec |
|---|---|---|
| A | Adopt Feather + STEMMA QT ecosystem | ✅ Yes |
| B | Replace in-enclosure power chain with USB-C input + Scanstrut external | ✅ Yes |
| C | Replace AC optos with Shelly Plus Plug S | ✅ Yes (both shore + gen) |
| D | Use pre-assembled DS18B20 leads; skip the RJ12 hub until Phase 10 | ✅ Yes |
| E | Use an off-the-shelf Feather IoT enclosure for v1; 3D-printed panel later | ✅ Yes for v1 |
| F | Keep Tier 0 LED+buzzer inside main enclosure; defer helm repeater (ATOM Echo) | ✅ Yes |
| G | Phase 8 GPS: use Adafruit Ultimate GPS FeatherWing (plug-in) | ✅ Yes |

If Pete approves these, I'll:
1. Rewrite `hardware-deep-dive.md` BOM sections as "superseded — see simplicity-review.md."
2. Update `architecture.md §2.5.1` power subsystem to "USB-C input; externalized to user's choice of supply."
3. Update `diagrams/hardware.md` and `diagrams/hardware-visuals.html` to reflect the Feather + Qwiic ecosystem.
4. Adjust `roadmap.md` Phase 3 from "full weekend + 72h soak" to "one evening + 72h soak."

---

## 10. Open Questions

1. **Path A vs B for enclosure** — off-the-shelf Amazon IoT box for v1, or wait for a 3D-printed design? Recommendation: A for v1.
2. **Does Pete have access to a 3D printer** (self, friend, library)? Drives whether Path B is even an option.
3. **Is the Scanstrut ROKK Charge+ the right marine USB-C source**, or does Pete prefer to hard-wire a cheap $20 Anker PowerDrive into a dedicated 12V feed? Difference is polish, not function.
4. **Shelly Plus Plug S in the gen outlet — is there a dedicated 120V outlet on the generator**, or does the gen feed the shore inlet via a transfer switch? If the latter, one Shelly on shore inlet + a separate method for genset (maybe the Victron SmartShunt's charge-current signature) suffices.
5. **Single-vendor lock-in to Adafruit** — acceptable, or should we mirror every part to a SparkFun Qwiic equivalent so there's a second source? Recommendation: document SparkFun equivalents in the BOM but buy from Adafruit by default.
