# EvenKeel — Hardware Diagrams (Simplified)

Mermaid diagrams reflecting the simplified Feather + STEMMA QT / Qwiic design locked by [`../simplicity-review.md`](../simplicity-review.md). Supersedes the v1.1 DevKitC-1 + M12 diagrams.

Render in GitHub, VS Code (with Mermaid extension), or at https://mermaid.live.

---

## 1. Physical Component Block Diagram (simplified)

```mermaid
flowchart TB
    subgraph Boat["⛵ Hunter 41DS"]
        direction TB

        subgraph Antenna["Antennas / RF"]
            VHF[VHF / AIS Antenna<br/>masthead]
            GPS_ANT[GPS Active Antenna<br/>Phase 8]
        end

        subgraph NavStation["Nav Station — Dry Locker"]
            dAISy[Wegmatt dAISy HAT<br/>AIS RX 161.975/162.025]
            Feather[("Adafruit ESP32-S3 Feather<br/>BoatMon-1<br/>+ Featherwing Proto")]
            BuzzLED[Tier 0: active buzzer<br/>+ red LED<br/>on proto board]
            Pi[Raspberry Pi 4 4GB<br/>+ 128GB USB SSD<br/>HA OS + Mosquitto]
            Router[X75 LTE Router<br/>4×4 MIMO<br/>WireGuard client]
        end

        subgraph Qwiic["Qwiic / STEMMA QT chain (plug-together I²C)"]
            INA[("INA228 Qwiic<br/>#5832 · 0x40<br/>house V + I")]
            BME[("BME280 Qwiic<br/>#2652 · 0x76<br/>cabin T/RH/baro")]
            ADS[("ADS1115 Qwiic<br/>#1085 · 0x48<br/>tanks · Phase 8")]
        end

        subgraph OneWire["1-Wire temperature"]
            DS[Adafruit #381<br/>DS18B20 3m waterproof lead<br/>× 3: cabin / engine / fridge]
        end

        subgraph Discrete["Discrete I/O on proto"]
            Float[Rule-A-Matic Plus<br/>bilge float switch]
            ADC[Starter batt V divider<br/>100k + 33k on A0]
        end

        subgraph ACSense["AC detection — outside enclosure"]
            ShellyShore[Shelly Plus Plug S<br/>SHORE<br/>UL-listed · native MQTT]
            ShellyGen[Shelly Plus Plug S<br/>GEN<br/>UL-listed · native MQTT]
        end

        subgraph Victron["Optional — Phase 7"]
            VicShunt[(("Victron SmartShunt<br/>BLE advertisement"))]
        end

        subgraph Power["Power — externalized"]
            Scanstrut[Scanstrut ROKK Charge+<br/>12V→USB-C PD<br/>marine-rated · outside enclosure]
            OptUPS[(("Optional Anker 733<br/>pass-through UPS")):::optional]
        end
    end

    VHF -->|coax / BNC| dAISy
    GPS_ANT -.->|coax / SMA| Feather

    dAISy -->|3-wire UART @38400<br/>soldered to proto| Feather

    INA <-->|STEMMA QT cable| Feather
    INA <-->|STEMMA QT cable| BME
    BME <-->|STEMMA QT cable| ADS

    DS -->|3× leads on proto<br/>+ 4.7kΩ pullup| Feather

    Float -->|2-wire on proto| Feather
    ADC -->|divider → A0 ADC| Feather

    VicShunt -.->|BLE advertisements| Feather

    Feather --> BuzzLED

    Feather -->|WiFi| Router
    Pi -->|WiFi| Router

    Scanstrut -->|USB-C cable| Feather
    OptUPS -.->|optional pass-through| Feather

    ShellyShore -.->|WiFi MQTT<br/>native| Router
    ShellyGen -.->|WiFi MQTT<br/>native| Router

    Router -.->|LTE + WireGuard| Cloud[("🏠 Home HA")]

    classDef optional stroke-dasharray: 5 5
    class OptUPS,GPS_ANT,ADS,VicShunt optional
```

**Changes from v1.1:**
- `DevKitC-1 + screw-terminal breakout` → **Adafruit ESP32-S3 Feather + Featherwing proto**
- I²C sensor chain is now **plug-together (STEMMA QT cables)** — zero soldering
- **No 12V wiring or power components inside the enclosure.** One USB-C input.
- **No opto-isolators inside the enclosure.** Two Shelly Plus Plug S externally via WiFi MQTT.
- M12 bulkheads eliminated — only USB-C, BNC, and a couple of grommets.

---

## 2. Power Distribution — Simplified

```mermaid
flowchart LR
    HB[12V House Bank<br/>300 Ah]
    SC[Scanstrut ROKK Charge+ USB-C<br/>marine-rated<br/>ISO 7637-2 surge protection<br/>12V/24V input · USB-C PD output]

    subgraph OptUPS[OPTIONAL UPS]
        UPS[Anker 733 PowerCore<br/>10 Ah pass-through<br/>~20h runtime]
    end

    USBC[USB-C cable<br/>short, quality]

    Feather[Adafruit Feather ESP32-S3<br/>BoatMon-1<br/>~100-400 mA @ 5V]

    HB --> SC
    SC -->|USB-C 5V PD| USBC
    SC -.->|alt via UPS| UPS -.-> USBC
    USBC --> Feather
```

**Daily energy budget (unchanged):**

| Load | Current | Ah/day |
|---|---|---|
| Feather + dAISy + sensors | ~250 mA @ 5V = ~110 mA @ 12V | ~2.6 |
| Pi 4 + SSD | ~300 mA @ 12V | ~7.2 |
| Shelly Plus Plug S × 2 | ~50 mA @ shore | — (from AC) |
| **Total** | **~410 mA @ 12V** | **~10 Ah/day** |

Negligible against a 300 Ah house bank (~3.3%/day).

---

## 3. ESP32-S3 Feather Pinout — BoatMon-1 (simplified)

```mermaid
flowchart LR
    subgraph Feather["Adafruit ESP32-S3 Feather (#5477)"]
        direction TB
        STEMMA[STEMMA QT<br/>JST-SH 4-pin<br/>SDA/SCL/3V3/GND]
        USB[USB-C port<br/>power + programming]
        RX[RX pin<br/>= GPIO38]
        D10[D10 = GPIO10]
        D11[D11 = GPIO11]
        D12[D12 = GPIO12]
        D13[D13 = GPIO13<br/>onboard LED]
        A0[A0 = GPIO17<br/>ADC1_6]
        D5[D5 = GPIO5]
        D6[D6 = GPIO6]
    end

    subgraph Proto["Featherwing Proto board"]
        PadsU[3-wire: dAISy UART]
        PadsF[2-wire: bilge float]
        PadsT[3-wire: Tier 0 LED+buzzer]
        Pad1W[3-wire: DS18B20 bus + pullup]
        PadAD[2-wire: V divider]
    end

    STEMMA -.->|Qwiic cable| QSENSORS[INA228 → BME280 → ADS1115]

    dAISy[dAISy HAT] -->|TX| RX
    dAISy -->|GND + 3V3| Proto

    PadsU <-.-> RX
    PadsF --> D10
    Float[Rule-A-Matic] --> PadsF
    PadsT --> D11
    PadsT --> D13
    Pad1W --> D6
    DS18B20s[3× DS18B20 leads] --> Pad1W
    PadAD --> A0
    Divider[100k + 33k] --> PadAD

    USB -->|5V| Feather
```

**One-time soldering — the Featherwing Proto session:**

| Joint group | Wires | Notes |
|---|---|---|
| dAISy UART | 3 (TX → RX pin, GND, 3V3) | soldered once, done forever |
| 1-Wire pullup | 2 (4.7 kΩ between data and 3.3V) | |
| DS18B20 leads | 3 lead-triplets on a single screw terminal | each lead has 3 wires |
| Bilge float | 2 (switch + GND) | |
| Tier 0 LED + resistor | 2 (GPIO + GND through 330Ω) | |
| Tier 0 buzzer | 2 (GPIO + GND) | active buzzer module |
| V divider | 3 (12V/sense/GND) | 100kΩ + 33kΩ |
| **Total** | **~17 joints** | One evening's work |

---

## 4. Enclosure — Off-the-shelf Feather IoT Box (Path A)

```
  ┌──────────────────────────────────────────────┐
  │  Feather-sized IoT enclosure (~$15)          │
  │  4.0" × 2.5" × 1.5", ABS/PLA, IP44 splash    │
  │                                              │
  │  Inside:                                     │
  │  ┌────────────────────────────────────────┐  │
  │  │ Adafruit ESP32-S3 Feather              │  │
  │  │ + Featherwing Proto (stacked)          │  │
  │  │ + dAISy HAT (stuck to side w/ standoffs)│ │
  │  └────────────────────────────────────────┘  │
  │                                              │
  │  Qwiic chain exits via grommet ↓             │
  │  ┌─ STEMMA QT cable → INA228                 │
  │  │                  → BME280                 │
  │  │                  → ADS1115 (Phase 8)      │
  │                                              │
  │  External connectors on enclosure wall:      │
  │    ① USB-C panel-mount (Adafruit #4218)      │
  │    ② BNC panel-mount (dAISy antenna)         │
  │    ③ 2-pin waterproof marine (bilge float)   │
  │    ④ Grommet × 1 (Qwiic chain + DS18B20s)    │
  │    ⑤ Grommet × 1 (Tier 0 cable, if external) │
  │                                              │
  │  Phase 8 only:                               │
  │    + SMA panel-mount (GPS antenna)           │
  └──────────────────────────────────────────────┘
```

Compare to v1.1 (Polycase WC-23F with DIN rail + 4-6× M12 bulkheads): half the size, no DIN rail, no custom M12 crimping, no conformal coating required for this environment (dry locker).

---

## 5. Connector Map (External) — simplified

| Port | Type | Function |
|---|---|---|
| — | USB-C panel jack | 5V power in (from Scanstrut or other source) |
| — | BNC panel jack | VHF/AIS antenna to dAISy |
| — | SMA panel jack | GPS antenna (Phase 8) |
| — | 2-pin waterproof | Bilge float switch |
| — | Grommet | Qwiic sensor chain + DS18B20 leads |
| — | Grommet | Tier 0 LED/buzzer pigtail (if external helm mount) |

Compared to v1.1: dropped 4 M12-A bulkheads (was $92 in parts) and 2 Deutsch DT connectors.

---

## 6. Sensor Wiring — fan-out diagram

```mermaid
flowchart LR
    Feather[Adafruit Feather ESP32-S3]

    Feather ==>|STEMMA QT cable| INA228[INA228 Qwiic<br/>house V + I]
    INA228 ==>|STEMMA QT cable| BME280[BME280 Qwiic<br/>cabin T/RH/baro]
    BME280 ==>|STEMMA QT cable| ADS1115[ADS1115 Qwiic<br/>tanks · Phase 8]

    Feather -->|D6 + 3.3V + GND<br/>4.7kΩ pullup| OneWireBus[1-Wire bus]
    OneWireBus --> DS1[DS18B20 cabin]
    OneWireBus --> DS2[DS18B20 engine bay]
    OneWireBus --> DS3[DS18B20 fridge]

    Feather -->|D10| Float[Bilge float switch]
    Feather -->|A0| VDivider[Starter V divider]
    Feather -->|D11| Buzzer[Active buzzer]
    Feather -->|D13| LED[Red LED]

    Feather <-.->|BLE · Phase 7| Victron[(Victron SmartShunt)]

    Feather <-->|RX ← TX<br/>UART @38400| dAISy[dAISy HAT]
    Antenna[VHF/AIS] -->|coax BNC| dAISy

    ShellyShore[Shelly Plus Plug S<br/>SHORE] -->|MQTT via boat WiFi| Broker[Mosquitto on Pi]
    ShellyGen[Shelly Plus Plug S<br/>GEN] -->|MQTT via boat WiFi| Broker
    Feather -->|MQTT via boat WiFi| Broker

    USB[Scanstrut USB-C<br/>outside enclosure] -->|USB-C cable| Feather
```

Everything on the thick edge is plug-in. Everything on the thin edge is one-time soldered on the Featherwing Proto.

---

## 7. HIL Test Rig — unchanged

The HIL rig architecture doesn't change with the simplified design. See the original bench-rig diagram in [`hardware-visuals.html` §7](hardware-visuals.html) and [`../../hil-rig/bom.md`](../../hil-rig/bom.md). If anything, HIL gets easier: the same Qwiic ecosystem + pre-wired float is what the rig stimulates.

---

## 8. What Changed (summary)

| Aspect | v1.1 | v2 simplified |
|---|---|---|
| MCU board | ESP32-S3-DevKitC-1 + CZH breakout | Adafruit ESP32-S3 Feather + Featherwing proto |
| I²C sensors | Hand-wired Amazon breakouts | Qwiic STEMMA QT (plug-in) |
| Power in enclosure | Fuse + TVS + cap + buck | USB-C jack only |
| Power outside | — | Scanstrut ROKK Charge+ (marine, commodity) |
| AC detection | 2× opto-isolator in enclosure | 2× Shelly Plus Plug S (UL-listed, MQTT) |
| Enclosure | Polycase WC-23F + DIN rail + 4-6× M12 bulkheads | Feather-sized IoT box + USB-C + BNC + grommets |
| Solder joints | ~50 | ~17 |
| Build time | 1 weekend + 72h soak | 1 evening + 72h soak |
| Phase 1–6 cost | $657 | $341 |

See [`../simplicity-review.md`](../simplicity-review.md) for the rationale.
