# EvenKeel On-Boat Local Dashboard — Options & Recommendation

**Document:** Companion to `sailboat-monitor-design.md` v1.0. Scope: dashboards physically ON the boat, usable with zero internet and zero dependency on the home HA instance.
**Author:** Research pass, April 2026.
**Status:** Design input — not yet locked.

---

## TL;DR — Recommendation Block

**RECOMMENDED PRIMARY (Pete's full build, Phase 10+):**
Tiered two-layer design:

1. **Always-on "critical status" layer** — a dedicated **ESP32-S3 + 4.3" or 5" IPS touch LCD** (Waveshare ESP32-S3-Touch-LCD-4.3 or Makerfabs equivalent) mounted at the nav station, running **ESPHome with `lvgl:` component**, subscribed to the SAME MQTT topics the boat already publishes. No additional server. ~500 mA @ 5 V (~2.5 W, 0.2 A @ 12 V via the existing buck). This is the "B&G Triton" equivalent: bilge / batteries / power source / anchor status, always lit.
2. **Rich dashboard layer** — `web_server:` component **already running on the BoatMon-1 ESP32-S3** (cost: zero incremental hardware, ~30 KB RAM). Crew opens it on a phone over boat WiFi at `http://boatmon-1.local` for graphs, AIS target list, tank history. This piggybacks on infrastructure that exists anyway.

Neither layer requires a Raspberry Pi, an on-boat HA instance, or cloud. Both continue to work if the LTE router is unplugged as long as the ESP32's fallback AP is up.

**RECOMMENDED MINIMAL (Phase 4-5, before Pete builds the LVGL panel):**
**ESPHome `web_server:` v3 ONLY.** Zero added hardware. Zero firmware complexity — six extra YAML lines. Crew visits `http://boatmon-1.local` on any phone on the boat LAN. Ship this with v1 and defer the dedicated panel to Phase 10.

**NOT RECOMMENDED:**
- On-boat Home Assistant on Pi Zero 2 W — underpowered, unsupported.
- On-boat Home Assistant on Pi 4/5 — adds ~3-5 W continuous, SD-card reliability risk at sea, duplicates the cloud HA, creates a state-sync problem with no good solution.
- Grafana — overkill, requires server, no advantage over HA or LVGL for this data volume.

---

## Comparison Matrix

| # | Option | Hardware $ | Idle draw @ 12 V | Sun-readable | Marine-ready | DIY effort | Offline? | Recommended for |
|---|---|---|---|---|---|---|---|---|
| 1 | ESPHome `web_server` on existing ESP32 | $0 | 0 mA add'l | N/A (phone) | via phone | trivial (YAML) | Yes | **Minimal baseline** |
| 2 | On-boat HA on Pi + wall tablet | $220-350 | 300-500 mA | Tablet-dep. | Tablet IP54 | medium-high | Yes | Over-engineered |
| 3 | On-boat HA on Pi + HDMI/DSI screen | $180-280 | 400-700 mA | 500-1000 nit | Marginal | medium | Yes | Over-engineered |
| 4 | Dedicated ESP32 + TFT (LVGL) | $40-100 | 150-250 mA | 300-1000 nit | IP-box mountable | medium | Yes | **Primary pick** |
| 5 | E-ink panel (Inkplate / Waveshare) | $50-150 | <5 mA avg | Excellent | Excellent | medium | Yes | Backup/critical |
| 6 | Grafana on Pi | $80-150 | 400-700 mA | phone | via phone | medium | Yes | Skip |
| 7 | PWA served by ESP32 (== #1) | $0 | 0 mA | phone | via phone | trivial | Yes | Same as #1 |
| 8 | NMEA2000 / SignalK bridge | N/A | N/A | N/A | N/A | hard | N/A | **Out of scope** (per design doc §2 non-goal) |

---

## Option 1 — ESPHome `web_server` (viewed on crew phones)

**What it is.** ESPHome has a built-in `web_server:` component that serves a LAN-only HTML/Lit-Element single-page app from the ESP32 itself. v3 of the frontend was rewritten for performance; sensor state streams over Server-Sent Events on `/events` with 10 s keepalive ([ESPHome docs](https://esphome.io/components/web_server/)). You get a list/card view of every entity the device publishes, with sliders for switches and graphs for sensors. Crew types `http://boatmon-1.local/` (mDNS) on any phone on the boat WiFi.

**Hardware:** none. Uses the BoatMon-1 ESP32-S3 that already exists.

**Power:** 0 mA incremental. The web_server enabled adds roughly 2-3 mA on the existing 3.3 V rail (noise floor).

**Software story:**
```yaml
web_server:
  version: 3
  port: 80
  include_internal: true
  ota: false        # OTA already gated via ESPHome API over WireGuard
  local: true       # serve JS/CSS from flash, no internet dep
```
`local: true` embeds the JS/CSS in firmware so the page works offline. This was explicitly added for "devices without internet access" use cases ([ESPHome web_server docs](https://esphome.io/components/web_server/)).

**Data path:** direct — the web UI reads from the ESP32's own in-RAM entity state. No MQTT round-trip, no HA, no cloud.

**Install / weatherproofing:** none. Phones stay in pockets, waterproof per the phone's rating.

**Pros:** zero cost, zero new hardware, zero new code, works the instant the boat WiFi is up, survives LTE outage. Fallback AP (already configured in design §6) means even a dead router is survivable — crew joins `BoatMon-Fallback` and still gets the dashboard.

**Cons:** phone in hand is not "glance-able." No always-on panel. Styling is ESPHome-generic, not curated. Adding a custom "How's My Boat" layout requires either a sibling ESPHome device, or dropping a single HTML file into flash and serving it from the web_server's static-file support.

**Verdict:** SHIP THIS FIRST. It's the minimum-viable local dashboard and it costs $0 and a YAML commit.

---

## Option 2 — On-boat Home Assistant on Pi + wall-mounted Android tablet

**Hardware:**
- Raspberry Pi 5 8 GB + official 27 W PSU + NVMe HAT + 256 GB NVMe — ~$130-160 (pishop.us, Digi-Key)
- 10" Android tablet (Amazon Fire HD 10 deals $100-150, or Lenovo Tab M10 $130-170)
- Wall mount, 5 V/2 A trickle charger wire, POE/USB power injector — $20-40
- Total: **$250-370**

**Power:** Pi 5 idles **~2.7 W headless** ([Jeff Geerling's Pi 5 review](https://www.jeffgeerling.com/blog/2023/reducing-raspberry-pi-5s-power-consumption-140x/)); with USB SSD, NVMe, and HA active load it's more like **4-6 W continuous** = **330-500 mA @ 12 V** through a buck. Tablet charging adds 5-15 W on top when its battery is topping up; at steady-state with screen on it's ~3 W.

**Display:** tablet-dependent. Fire HD 10 peaks ~400 nits — readable in cabin, not in cockpit sun. Viewing angle is fine (IPS).

**Software:** HA OS on Pi (HAOS supports Pi 5 officially as of 2026 — see [Seeed / HA community](https://www.seeedstudio.com/blog/2026/04/13/running-home-assistant-on-raspberry-pi/)); MQTT broker is the local Mosquitto add-on; ESP32 publishes locally; tablet runs HA Companion app or Fully Kiosk Browser to the Pi.

**State sync to home HA:** this is the hard part. Options:
- **Mosquitto bridge**: local boat broker bridges a topic subset to the OCI broker; home HA continues to subscribe to OCI. Both HAs see the same data. Straightforward ~10 lines of config ([Mosquitto bridge docs](http://www.steves-internet-guide.com/mosquitto-bridge-configuration/)).
- **HA-to-HA via remote_homeassistant custom integration**: brittle, deprecated direction.
- **Nabu Casa**: disallowed per constraints.
- **WireGuard + REST**: works but a hack.

The bridge works, but it means you now run **two HA instances** with the same data. Automations fire twice unless you carefully split responsibilities. Config drift will bite.

**Install / weatherproofing:** Pi lives in the dry locker with BoatMon. Tablet at the nav station — not IP-rated. Splash is survival-grade only.

**Pros:** familiar Lovelace UX; reuses "How's My Boat" card design; graphs, history, map tiles cached offline.

**Cons:** power-hungry, SD/SSD reliability at sea is a real concern (humidity, vibration, unclean shutdowns on power cut — even with the pass-through UPS the Pi gets killed if the cell dies first), duplicates cloud HA, state-sync complexity, tablet not marine.

**Verdict:** **skip.** The complexity/power cost is not justified when Option 1 + Option 4 cover everything.

---

## Option 3 — On-boat HA on Pi with direct HDMI/DSI touchscreen at nav

**Hardware:**
- Raspberry Pi 4 4 GB + PSU — ~$55-70
- Official 7" DSI touchscreen (800×480, ~350 nits) — $80 (raspberrypi.com)
- Or SunFounder 10" IPS HDMI touchscreen — $90-130 (Amazon)
- VESA mount / nav-station bracket — $15
- Total: **$150-280**

**Power:** Pi 4 idle ~0.6 W, with HA load and 7" DSI lit ~4-5 W = **330-420 mA @ 12 V**. 10" HDMI touchscreen adds another 3-5 W.

**Display:** official 7" DSI is **dim (~350 nits)** — acceptable at the nav station, unreadable outside. Waveshare and SunFounder HDMI panels range 400-1000 nits; a 1000-nit "sunlight-readable" 7" HDMI panel is available from Waveshare for ~$160 but now you're approaching a dedicated chartplotter's price.

**Night mode:** HA's `card-mod` theme can do red-on-black at the browser level, but the backlight itself is still white LEDs — red tint is cosmetic, not radiometric. True night-vision preservation (matching Raymarine i70, which dims backlight AND switches palette — per [Panbo / Raymarine manual](https://panbo.com/raymarine-i70-vs-garmin-gmi-10-mission-accomplished/)) requires a monochrome-red OLED or an LCD with a physical red filter. Not achievable with a stock Pi screen.

**Pros:** HA frontend is polished; graphs; single screen for everything.

**Cons:** everything in Option 2, plus no tablet portability. Always-on backlight eats power. Boot time 45-90 s after any power blip.

**Verdict:** **skip.**

---

## Option 4 — Dedicated ESP32-S3 + touch LCD, LVGL via ESPHome (RECOMMENDED PRIMARY)

This is the "marine instrument head" equivalent, and it's where the win is.

### Candidate hardware

| Board | Display | Resolution | Brightness | Price | Notes |
|---|---|---|---|---|---|
| **Waveshare ESP32-S3-Touch-LCD-4.3** | 4.3" IPS, capacitive touch | 800×480 | ~350 nit typ | **~$45** (Waveshare/Amazon) | Best size-for-cost; onboard CAN + RS485 (future NMEA bridge) |
| Waveshare ESP32-S3-Touch-LCD-5 | 5" IPS cap touch | 800×480 | ~400 nit | ~$55 | Slightly better for distance viewing |
| **Waveshare ESP32-S3-Touch-LCD-7** | 7" IPS cap touch | 800×480 | ~400 nit | ~$75 | Too big for nav station likely; 16 MB flash / 8 MB PSRAM |
| Waveshare ESP32-S3-Touch-LCD-7B | 7" IPS cap touch | 1024×600 | ~400 nit | ~$85 | Higher res, same frame |
| Makerfabs ESP32-S3 Parallel TFT 4.3" | 4.3" 480×272/800×480 | varies | ~400 nit | ~$45-60 | Alt to Waveshare, 16-bit parallel is snappier |
| **M5Stack CoreS3** | 2.4" IPS + enclosed case | 320×240 | ~400 nit | ~$50 | Comes as a finished product in a plastic case |
| M5Stack Tough (ESP32 classic) | 2.4" IPS | 320×240 | — | ~$50 | **IP54-rated** enclosure |
| LilyGO T-Display-S3 | 1.9" IPS | 170×320 | ~400 nit | ~$20 | Too small for a dashboard |
| Cheap Yellow Display (ESP32-2432S028R) | 2.8" TFT resistive | 240×320 | ~300 nit | **~$15** | Unbeatable price for bench; resistive tolerates wet fingers |

**Pick for the boat:** **Waveshare ESP32-S3-Touch-LCD-4.3** (or the 5"). Rationale: big enough to be glance-able at 1 m; onboard PSRAM handles LVGL double-buffering cleanly; onboard CAN opens a later NMEA2000 stretch goal without replacing hardware.

### Power @ 12 V

- Board idle w/ backlight off: ~80 mA @ 5 V = 33 mA @ 12 V
- Typical operation (backlight 50%, WiFi, LVGL rendering): **~500-700 mA @ 5 V = 210-290 mA @ 12 V** (~3 W)
- Backlight alone is the dominant draw — dim to 20% at night and you save ~200 mA on the 5 V rail

### Software story

**ESPHome's `lvgl:` component** (stable since 2024.6) drives the display with declarative YAML widgets — pages, labels, buttons, meters, charts. No C code required. The device can independently subscribe to MQTT topics published by BoatMon-1:

```yaml
mqtt:
  broker: boatmon-1.local
  on_message:
    - topic: boat/hunter41/bilge/water_detected
      then:
        - lvgl.label.update:
            id: bilge_label
            text: !lambda 'return x == "1" ? "WATER" : "DRY";'
lvgl:
  pages:
    - id: home_page
      widgets:
        - label:
            id: bilge_label
            text: "DRY"
```

Alternative: run `api:` to the existing BoatMon-1 via **ESPHome native API** (binary, more efficient than MQTT, auto-reconnect built in). This avoids a broker dependency when the LTE router is down.

### Night / red mode

LVGL supports runtime themes. Wire a GPIO button ("NAV/NIGHT") that swaps a red-on-black theme AND reduces backlight PWM to 5-10%. For true red-preserves-dark-vision, add a physical red gel film over the panel — crude but effective. The i70's dedicated red LED backlight remains the gold standard; a DIY IPS won't fully match it.

### Install / weatherproofing

Mount inside nav station at the chart table (dry). If you want a cockpit repeater, put the unit behind a marine instrument cutout with a polycarbonate window and a silicone bezel. Cable glands for USB-C and GND, identical pattern to BoatMon-1's enclosure. For a truly IP-rated enclosed unit use the **M5Stack Tough** (IP54) at the cost of a smaller screen.

### Pros

- Glance-able, always on
- ~$45-80 all-in
- Same firmware framework (ESPHome YAML) as BoatMon-1 — Pete learns nothing new
- MQTT/API means it auto-reflects every new sensor added to BoatMon-1
- Survives total cloud + router outage

### Cons

- Not sunlight-readable in full cockpit sun (no consumer IPS at this price is)
- DIY enclosure work for a nice marine finish
- LVGL YAML is verbose; a 5-page dashboard is 300-500 lines

---

## Option 5 — E-ink panel for always-on critical status

**Candidates:**

| Board | Size | Price | Notes |
|---|---|---|---|
| **Inkplate 6** | 6" / 800×600 mono | ~$110 | ESP32, 22 µA sleep, weeks on a battery |
| Inkplate 6 COLOR | 6" / 600×448 7-color | ~$150 | 18 µA sleep, slow refresh (~15 s) |
| Inkplate 10 | 9.7" / 1200×825 mono | ~$170 | Biggest, best for full status page |
| Waveshare 7.5" e-Paper HAT + ESP32 | 7.5" / 800×480 mono | ~$55 + ESP32 | 14 µA sleep, DIY |

**Power:** Inkplate 6 averages ~20 µA sleep; draws ~80-100 mA for ~1-2 s during refresh. If you refresh every 60 s with real data: average < 2 mA @ 5 V = **<1 mA @ 12 V**. Practically zero.

**Readability:** e-paper is **excellent in any light including direct sun** — this is where it beats every LCD. No glare, no viewing-angle issue. Trade-off: no backlight, so useless in a dark cabin without ambient or a front-light (Inkplate 6 PLUS has a front-light).

**Use case fit:** perfect for a **nav-station always-on "critical-status" strip**: "BOAT ONLINE | BATT 12.8 V | BILGE DRY | ON SHORE | 72 °F cabin". Refreshes once a minute. Sips power. Cannot do graphs or interactivity well.

**Verdict:** **defer to stretch phase.** Not first-build. If Pete loves the LVGL panel, add an Inkplate 6 later as the "underway quiet mode" display.

---

## Option 6 — Grafana on a local Pi

**Cost:** Pi 4 $55 + screen $80-130 = same ballpark as Option 3.

**Power:** same as Option 3.

**Software:** Mosquitto → Telegraf → InfluxDB → Grafana, all on one Pi via Docker.

**Why not:** duplicates everything HA already does (worse UX for state, better UX for graphs). No actions/automations story. No mobile app. Adds a second backend to maintain. HA + InfluxDB integration gives you Grafana-style graphs inside HA if you want them.

**Verdict:** **skip** unless Pete specifically wants Grafana aesthetics.

---

## Option 7 — PWA served by ESP32 or on-boat Pi

This is Option 1 dressed up. ESPHome's web_server can be bookmarked as a PWA on iOS/Android ("Add to Home Screen") giving a full-screen icon. With `local: true` it runs offline.

If Pete wants a custom-designed "How's My Boat" card rather than the generic ESPHome frontend, the cleanest path is: write a single static HTML file, embed it as a static asset on a second "dashboard" ESPHome node, fetch MQTT state via WebSocket through Mosquitto's WS listener. ~100 lines of vanilla JS + CSS, no framework.

**Verdict:** **viable Phase 10 upgrade** if Option 1's generic frontend is unsatisfying.

---

## Option 8 — NMEA2000 / SignalK bridge (mentioned only)

Per the design doc §2 **explicit non-goal**. Hunter 41DS's existing plotter is already the navigation display; EvenKeel data is house-system telemetry, not navigation.

Brief note for future-proofing: the Waveshare ESP32-S3-Touch-LCD-4.3 has onboard CAN, so a Phase 11+ addition of NMEA2000 sender (via `canbus:` in ESPHome, + esp32-nmea2000 lib) is possible without replacing hardware. **Not designed for here.**

---

## Tiered Dashboard Architecture (recommended design)

Concrete recipe:

```
┌──────────────────────────────────────────────────────┐
│  Tier 0 — "Silent alarm" (always on)                 │
│  Single discrete red/green LED + piezo buzzer        │
│  Driven directly from BoatMon-1 GPIO                 │
│  Watches: bilge_water, batt<11.8, boatmon_online     │
│  Power: <10 mA @ 5 V                                 │
│  Cost: $3 (LED + resistor + buzzer)                  │
└──────────────────────────────────────────────────────┘
                     │
┌──────────────────────────────────────────────────────┐
│  Tier 1 — "At-a-glance" (always on at nav station)   │
│  Waveshare ESP32-S3-Touch-LCD-4.3 running ESPHome    │
│  + lvgl: component                                   │
│  Single-page "How's My Boat" layout:                 │
│    • BOAT: ONLINE / OFFLINE banner                   │
│    • PWR: SHORE / GEN / BATT (icon + colour)         │
│    • BATT: 12.8 V / 85% SoC (bar + colour)           │
│    • BILGE: DRY / WET (big glyph)                    │
│    • CABIN/ENGINE/FRIDGE temps (3 tiles)             │
│    • ANCHOR: SET / DRIFT badge (Phase 9)             │
│  Night: red/black theme + 5% backlight on toggle     │
│  Power: ~250 mA @ 12 V                               │
│  Cost: $45-60 + enclosure                            │
└──────────────────────────────────────────────────────┘
                     │
┌──────────────────────────────────────────────────────┐
│  Tier 2 — "Rich dashboard" (on demand, phone)        │
│  ESPHome web_server v3 on BoatMon-1                  │
│  Bookmark as PWA on crew phones                      │
│  Full entity list, graphs, AIS target table, config  │
│  Power: $0 incremental                               │
│  Cost: $0                                            │
└──────────────────────────────────────────────────────┘
```

**Design inspiration map** — what each tier borrows from:
- Tier 0 = **Victron BMV bilge-alarm pattern**: single piezo, non-negotiable.
- Tier 1 = **B&G Triton 2 / Raymarine i70s** — single-screen curated status, big glyphs, night-mode toggle.
- Tier 2 = **Victron Cerbo GX VRM portal / GX Touch 50** — detailed drill-down.

**Is the tier-0 LED+buzzer worth the complexity?** Yes, marginally: it's ~$3 and protects the "I'm sinking but the LCD is asleep / firmware hung" failure mode. Wire it off GPIO directly from BoatMon-1 (not the LVGL head) so that an LVGL firmware crash doesn't disable the alarm.

**Night / red-mode final word:** The Tier 1 LCD gets red theme + PWM-dimmed backlight + optional physical red gel. Matches i70 functionally at 1/10 the cost, but does not match radiometrically. If Pete is a serious night sailor, add an Inkplate 6 as a true emission-free repeater above the companionway. Stretch phase.

**Waterproofing:** Tier 0 LED/buzzer behind a clear polycarbonate overlay at helm (IP65 achievable with potting). Tier 1 LCD at nav station (inside boat, IP44 splash sufficient). Tier 2 is the crew's phone — already personal IP-rated.

---

## "At-a-glance" content specification (Tier 1 LCD layout)

Drawn from B&G Triton 2, Raymarine i70s, Garmin GMI-20, Victron GX Touch 50. Ordered by criticality:

| Row | Metric | Good | Warn | Bad | Notes |
|---|---|---|---|---|---|
| Header | Boat name + online status | "HUNTER 41DS • ONLINE" | — | "OFFLINE 12m" red banner | heartbeat <5m |
| 1 | Bilge | "DRY" green | — | "WATER" flashing red | biggest glyph |
| 2 | Power source | "SHORE" green / "GEN" amber | — | "BATTERY" red at slip | icon + word |
| 3 | House batt | 12.6 V (or 85% SoC if Victron BLE up) | 12.0-12.4 | <12.0 | bar meter |
| 4 | Start batt | 12.4+ V | 12.0-12.4 | <12.0 | single number |
| 5 | Temps — tile row | each zone green in band | yellow | red | 3 tiles Phase 5, 10 tiles Phase 10 |
| 6 | Anchor / Position (Phase 9) | "SET 12 m" | "DRIFT 20 m" | "DRAG 52 m" red | only when armed |
| Footer | Clock, RSSI, uptime | — | — | — | small |

---

## Open Questions

1. **Enclosure finish:** custom nav-station cutout or surface-mounted Polycase? (Aesthetics vs effort.)
2. **Tier 0 hardware placement:** at nav station only, or also at helm?
3. **Backlight auto-dim:** ambient-light sensor, or manual toggle only?
4. **Red gel film choice:** verify colors don't wash out before committing.
5. **LVGL font size:** prototype before cutting holes.
6. **Tier 1 data source:** direct MQTT to broker, or local ESPHome native API to BoatMon-1? Recommend **native API with MQTT fallback**.
7. **Does Pete want the Tier 1 panel at all in v1**, or does Option-1-only suffice for the first season?
8. **Second LVGL panel at helm** (Phase 11+)? Same firmware, different mount.
9. **Safety-ESP32 watchdog** — should it drive Tier 0 independently?
10. **Fire tablet option:** if Pete wants a Kelly-style tablet on the boat, Option 1's PWA on a cheap Fire HD 10 in kiosk mode.

---

## Sources

- [ESPHome web_server component docs](https://esphome.io/components/web_server/)
- [Waveshare ESP32-S3-Touch-LCD-7 wiki](https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-7)
- [Random Nerd Tutorials — CYD ESP32-2432S028R](https://randomnerdtutorials.com/cheap-yellow-display-esp32-2432s028r/)
- [M5Stack CoreS3 product page](https://shop.m5stack.com/products/m5stack-cores3-esp32s3-iotdevelopment-kit)
- [Soldered Inkplate 6](https://soldered.com/products/inkplate-6-6-e-paper-board)
- [Jeff Geerling — Pi 5 idle power consumption](https://www.jeffgeerling.com/blog/2023/reducing-raspberry-pi-5s-power-consumption-140x/)
- [Victron Cerbo GX product page](https://www.victronenergy.com/communication-centres/cerbo-gx)
- [Raymarine i70s product page](https://www.raymarine.com/en-us/our-products/marine-instruments/i70s-series/i70s-instrument)
- [Steves Internet Guide — Mosquitto bridge configuration](http://www.steves-internet-guide.com/mosquitto-bridge-configuration/)
