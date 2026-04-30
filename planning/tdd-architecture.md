# EvenKeel Test Harness — TDD Architecture

A natural-language, dual-mode (virtual + live-integration) test architecture for the EvenKeel DIY ESP32-based sailboat monitoring system.

---

## A. BDD / Natural-Language Test Frameworks

The test steps need to drive four very different surfaces: ESPHome firmware (via MQTT and serial), a Mosquitto broker, Home Assistant (REST/WebSocket + Lovelace UI), and a browser dashboard. The framework has to be comfortable in Python (because every one of those surfaces has a mature Python client) and produce feature files a non-programmer can read.

### Candidates evaluated

**pytest-bdd** — https://github.com/pytest-dev/pytest-bdd
Gherkin frontend on top of pytest. Steps are plain Python fixtures. Runs inside the same process as every Python tool you want (`paho-mqtt`, `aiomqtt`, `homeassistant` REST client, `playwright`, `pyserial`). You get pytest's parametrization, fixtures, markers (`@virtual`, `@hil`, `@live`), and parallelism for free. Reports via `pytest-html` or Allure.
- Pros: one runner, full Python ecosystem, trivial to share step definitions across modes, huge community, excellent CI story.
- Cons: Gherkin parser is slightly less strict than Cucumber's.

**behave** — https://github.com/behave/behave
The "closest-to-Cucumber" pure-Python BDD runner. Cleaner separation between steps and tests than pytest-bdd, nicer hooks model.
- Pros: Cleanest Gherkin ergonomics.
- Cons: No native pytest integration — you lose fixtures, parametrization, parallelism.

**Cucumber (Node/Java/Ruby)** — canonical implementation, but step definitions would live outside Python. Re-implementing MQTT + HA clients in JS or Ruby is significant friction. **Skip.**

**Robot Framework** — https://github.com/robotframework/robotframework
Keyword-driven rather than strict Gherkin. Rich library ecosystem: `MQTTLibrary`, `RequestsLibrary`, `Browser` (Playwright), `SerialLibrary`. Reports are beautiful out of the box.
- Pros: Best-in-class reports, strong library coverage, non-programmer-friendly syntax.
- Cons: Non-Gherkin by default; fewer examples for `pytest-homeassistant-custom-component`.

**Playwright + Cucumber-JS** — good if the dashboard tests dominated. For sensor/MQTT/HA-state tests you'd be back to shelling out to Python. Reserve for UI-only layer if ever needed.

### Recommendation: **pytest-bdd**

1. Every other tool Pete will touch (Wokwi CLI, HA test helpers, aiomqtt, Playwright) lives in pytest-world.
2. Feature files are plain Gherkin — a non-programmer reader sees the same thing a behave user would.
3. Adapters (virtual/HIL/live) map cleanly onto pytest fixtures selected by CLI flag or tag.
4. CI integration on GitHub Actions is trivial.

Robot Framework is the credible runner-up; choose it only if pytest-bdd's scenario-step linkage proves clumsy.

---

## B. Simulation Layers — Building the Virtual Boat

### ESP32 firmware simulators

| Tool | URL | Fit for EvenKeel |
|---|---|---|
| **Wokwi** | https://wokwi.com / https://github.com/wokwi/wokwi-cli | **Best fit.** Supports ESP32-S3, DS18B20, I2C peripherals, UART, buttons. VS Code extension, headless CLI for CI, HTTP/serial API for scripted stimulus. Free for OSS/CI minutes. |
| QEMU ESP32 | https://github.com/espressif/qemu | Boots ESP-IDF, peripheral model thin. No first-class DS18B20, BLE, or WiFi radio. Useful for low-level firmware unit tests only. |
| ESP-IDF Linux target | Compiles IDF components for host. ESPHome isn't portable. | Unit tests only. |
| Renode | Strong peripheral modeling, but ESP32-S3 support limited and ESPHome/Arduino-IDF isn't a target. | Skip. |
| ESPHome "compile-only" | `esphome compile boat-mon.yaml` | Lint step. |

### Can ESPHome firmware run under Wokwi?

Yes, with caveats. Use `luar123/esphome-wokwi-integration` (https://github.com/luar123/esphome-wokwi-integration) plus the Wokwi VS Code extension and `wokwi.toml` pointing at ESPHome's build output.

**Limitations that bite this project:**
- No BLE radio simulation — Phase 7 Victron BLE must be faked at a different layer (MQTT test-mode topic).
- WiFi emulated via Wokwi-hosted gateway with constrained egress; for MQTT-over-TLS point firmware at a local Mosquitto reachable via `host.docker.internal`.
- 1-Wire DS18B20 supported; INA226 generic I2C model needs a tiny Wokwi "chip" written in C or via chips-api.
- No radio-layer sim for dAISy UART input — fine, it's plain serial. Feed a Wokwi "UART source" replaying AIVDM.
- GPS NMEA: same trick — UART source replays canned NEO-M9N sentences.

### Virtual sensor injection

Two approaches, mix freely:

1. **Simulator-level injection.** Wokwi's automation API sets GPIO levels, drives UART bytes, sets analog pin voltages.
2. **Firmware-level "test mode."** ESPHome `mqtt.subscribe` to `boat/hunter41/test/<sensor>` on a retained topic. A `template` sensor wraps each real sensor in a `lambda` returning the injected value when a global `test_mode` flag is on, else the hardware reading. **Key enabler for live-integration tests on deployed hardware** where you can't physically pour water on the bilge switch.

### MQTT broker in test

- **mosquitto:2** Docker image, binds `127.0.0.1:1883` (test) and `:8883` (TLS) with a self-signed cert.
- Python client: **aiomqtt** (https://github.com/empicano/aiomqtt).

### Home Assistant in test

- `homeassistant/home-assistant:stable` Docker image with minimal `configuration.yaml` pointing at the test broker. Exposed on `localhost:8123`.
- Long-lived token baked into test fixtures; tests hit `/api/states/<entity_id>` and `/api/services/<domain>/<service>` via `httpx`.
- For **automation** testing, WebSocket API (`/api/websocket`) asserts notification events and listens to `state_changed`.
- `pytest-homeassistant-custom-component` (https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) is for writing custom HA components; not needed unless Pete ends up writing one.

### Browser automation for dashboards

- **Playwright** (https://github.com/microsoft/playwright-python) over Selenium. Auto-wait, trace viewer.
- Screenshot comparison: **pytest-playwright-snapshot** (https://github.com/mxschmitt/pytest-playwright-snapshot) or hand-roll with `pixelmatch-py`.
- Log in once per session via `auth/login_flow` WebSocket API, store storage state, reuse.

### Simulating AIS NMEA

- Script streams canned AIVDM lines to TCP on loopback and/or replays them into Wokwi's UART source.
- Public corpora: **pyais** samples (https://github.com/M0r13n/pyais), gpsd test AIS data, live snapshots from aisstream.io.
- Library to generate synthetic sentences: **pyais** `encode_dict()`.

### Simulating GPS

- **gpsfake** (gpsd) replays NMEA logs over a pty — bridge pipes the pty to Wokwi's UART source or physical UART in HIL.
- Or Python script emits `$GPRMC`/`$GPGGA` at 1 Hz from a scripted track.

### Simulating BLE Victron

- Fabian-Schmidt's `esphome-victron_ble` (https://github.com/Fabian-Schmidt/esphome-victron_ble). For virtual mode, bypass BLE: firmware reads from `boat/hunter41/test/victron/*` MQTT topics in test mode.
- For HIL on real hardware: second ESP32 (the HIL rig) advertising legitimate Victron BLE frames.

---

## C. EvenKeel Test Harness — Proposed Architecture

### Layer diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Gherkin .feature files  (tests/features/*.feature)              │
│    bilge_alarm.feature, battery_low.feature, ais_forwarding...  │
└──────────────────────────┬──────────────────────────────────────┘
                           │  pytest-bdd step bindings
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step definitions  (tests/steps/*.py)                            │
│   "when the bilge switch goes high"  --> adapter.set_bilge(True)│
└──────────────────────────┬──────────────────────────────────────┘
                           │  adapter interface (abstract)
                           ▼
┌─────────────────┬─────────────────┬─────────────────────────────┐
│ VirtualAdapter  │ HilAdapter      │ LiveIntegrationAdapter      │
│ - Wokwi CLI     │ - serial cmds   │ - MQTT test-mode topics     │
│ - UART replay   │   to HIL rig    │   to deployed firmware      │
│ - MQTT inject   │ - GPIO relay    │ - read back real telemetry  │
└─────────────────┴─────────────────┴─────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Targets                                                         │
│   ESPHome firmware   Mosquitto broker   Home Assistant   dashbd │
└─────────────────────────────────────────────────────────────────┘
```

The adapter is selected by a pytest option: `pytest --mode=virtual|hil|live`, defaulting to `virtual`. A single `conftest.py` wires the `boat` fixture to the correct adapter. **Step definitions never know which mode is active.**

### Adapter interface contract (Python Protocol)

```python
class BoatAdapter(Protocol):
    async def startup(self): ...
    async def shutdown(self): ...

    # Stimuli
    async def set_bilge(self, wet: bool): ...
    async def set_shore_power(self, on: bool): ...
    async def set_generator(self, on: bool): ...
    async def set_house_voltage(self, volts: float): ...
    async def set_starter_voltage(self, volts: float): ...
    async def set_temperature(self, zone: str, celsius: float): ...
    async def inject_victron(self, soc: float, current: float, ttg_min: int): ...
    async def replay_ais(self, path: pathlib.Path, rate: float = 1.0): ...
    async def set_gps_track(self, track: list[tuple[float, float, float]]): ...

    # Observations (adapter-transparent: HA is always the source of truth)
    async def entity_state(self, entity_id: str) -> str: ...
    async def wait_for_notification(self, predicate, timeout: float): ...
    async def mqtt_last(self, topic: str) -> bytes: ...
```

### Firmware "test mode"

A retained MQTT topic gates injection:

```yaml
# packages/test_mode.yaml  — included only with -D ENABLE_TEST_MODE
globals:
  - id: test_mode_active
    type: bool
    restore_value: yes
    initial_value: 'false'

mqtt:
  on_message:
    - topic: boat/hunter41/test/enable
      then:
        - globals.set:
            id: test_mode_active
            value: !lambda 'return x == "ON";'
    - topic: boat/hunter41/test/bilge
      then:
        - lambda: |-
            if (id(test_mode_active)) {
              id(bilge_template).publish_state(x == "ON");
            }
```

**Security implications — treat seriously:**
1. Include `test_mode.yaml` only under a build flag. Production builds compile without it.
2. If included, require BOTH (a) a signed "enable" token on `boat/hunter41/test/enable` (HMAC with a secret in `secrets.yaml`) and (b) firmware auto-disables after 10 min of no `keepalive` topic activity.
3. Restrict the test-topic tree via Mosquitto ACL — only test user/cert can publish there.
4. Fire a conspicuous HA notification ("BOAT IS IN TEST MODE") any time the retained "enable" flag is ON so Kelly never misreads a fake alarm — or worse, sees fake "dry" while it's really wet.
5. Log every test-mode injection to an audit topic HA records permanently.

### Scenario organization

Organize by **user-visible capability**, cross-cut by **phase** with tags:

```
tests/features/
  alerts/
    bilge_alarm.feature            @phase6 @alerts
    battery_low.feature            @phase6 @alerts
    offline_watchdog.feature       @phase6 @alerts
    shore_power_lost.feature       @phase6 @alerts
    anchor_drag.feature            @phase9 @alerts @gps
  telemetry/
    temperature_reporting.feature  @phase5
    battery_voltage.feature        @phase5
    victron_soc.feature            @phase7 @ble
  ais/
    local_tcp_stream.feature       @phase1 @ais
    cloud_relay_forward.feature    @phase2 @ais @cloud
  dashboard/
    kelly_card_online.feature      @phase5 @ui
    kelly_card_alerts.feature      @phase6 @ui
  resilience/
    wifi_reconnect.feature         @phase3 @resilience
    mqtt_reconnect.feature         @phase3 @resilience
    power_cycle.feature            @phase3 @resilience
```

Tags let Pete run `pytest -m phase5` during phase 5 commissioning.

### Sample `.feature` — Gherkin a non-programmer can read

```gherkin
# tests/features/alerts/bilge_alarm.feature

Feature: Bilge water alarm
  As the boat owner, I want to be alerted whenever water is detected
  in the bilge so that I can respond before damage occurs.

  Background:
    Given the boat monitoring system is online
    And Kelly's "How's My Boat" card shows "Dry"

  @phase6 @critical
  Scenario: Bilge float switch triggers a notification
    When the bilge float switch reports water for 10 seconds
    Then within 30 seconds Home Assistant entity "binary_sensor.boatmon_bilge_water" should be "on"
    And Pete should receive a push notification containing "WATER DETECTED"
    And Kelly should receive a push notification containing "WATER DETECTED"
    And the home speakers should announce "Bilge water detected on the boat"
    And Kelly's "How's My Boat" card should show "WATER DETECTED" in red

  @phase6
  Scenario: Brief float chatter does not trigger an alarm
    When the bilge float switch reports water for 2 seconds
    And the bilge float switch reports dry
    Then no bilge notification should be sent within 60 seconds
    And Kelly's "How's My Boat" card should still show "Dry"

  @phase6 @recovery
  Scenario: Bilge alarm clears when water recedes
    Given the bilge alarm is active
    When the bilge float switch reports dry for 5 minutes
    Then Home Assistant entity "binary_sensor.boatmon_bilge_water" should be "off"
    And Kelly's "How's My Boat" card should show "Dry"

  @phase6 @offline
  Scenario: Bilge alarm fires even if boat briefly disconnects
    Given the boat's MQTT connection has been offline for 2 minutes
    When the boat reconnects
    And the firmware replays a retained bilge-water event
    Then Pete should receive a push notification containing "WATER DETECTED"
```

AIS end-to-end:

```gherkin
# tests/features/ais/cloud_relay_forward.feature

Feature: AIS sentences reach aisstream.io via the cloud relay

  @phase2 @ais @cloud
  Scenario: Class B target from Lake Erie sample is forwarded
    Given the AIS feed replays "samples/lake_erie_10min.aivdm" at real speed
    When 60 seconds pass
    Then the local TCP port 6638 has emitted at least 5 AIVDM sentences
    And the cloud relay log shows at least 5 forwarded messages
    And the test subscriber on aisstream.io has received MMSI 367123456
```

Dashboard-only:

```gherkin
# tests/features/dashboard/kelly_card_alerts.feature

Feature: Kelly's dashboard reflects alerts immediately

  @phase6 @ui
  Scenario: Dashboard turns red when bilge alarm fires
    Given Kelly's dashboard is open in a browser
    And the "Bilge" tile is green showing "Dry"
    When the bilge float switch reports water for 10 seconds
    Then within 5 seconds the "Bilge" tile should be red showing "WATER DETECTED"
    And a screenshot of the dashboard should match "snapshots/kelly_card_bilge_wet.png"
```

---

## D. Concrete Toolchain Recommendations

| Concern | Choice | Why |
|---|---|---|
| BDD framework | **pytest-bdd** | Same runner as every downstream Python tool. |
| Firmware simulator | **Wokwi** (CLI + VS Code ext) | Only serious option with ESP32-S3, DS18B20, UART replay, headless CI. |
| MQTT broker (test) | **mosquitto:2** in Docker | Matches production. |
| Home Assistant (test) | **homeassistant/home-assistant:stable** | Runs actual HA automations. |
| MQTT client in tests | **aiomqtt** | Async, clean context manager. |
| Dashboard automation | **Playwright** via `pytest-playwright` | Auto-wait, trace viewer. |
| AIS stimuli | **pyais** + canned aisstream captures | Same decoder as downstream. |
| GPS stimuli | **gpsfake** or scripted NMEA | Covers anchor-drag scenarios. |
| Victron stimuli | MQTT inject (virtual) / BLE advertiser (HIL) | Pragmatic around Wokwi's missing BLE. |
| CI | **GitHub Actions**: Wokwi CLI + docker-compose + pytest-bdd | Free for public repo. |

### CI approach (GitHub Actions)

```yaml
name: tests
on: [push, pull_request]
jobs:
  virtual:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r tests/requirements.txt
      - run: docker compose -f tests/docker/compose.yml up -d mosquitto homeassistant
      - uses: esphome/esphome-action@v2
        with: { yaml-file: firmware/boat-mon.yaml }
      - uses: wokwi/wokwi-ci-action@v1
        with:
          token: ${{ secrets.WOKWI_CLI_TOKEN }}
          path: tests/wokwi
          timeout: 600000
      - run: pytest --mode=virtual -m "not hil and not live"
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: playwright-trace, path: tests/.playwright }
```

A second workflow on a self-hosted runner in Pete's garage runs `--mode=hil` when `main` is tagged.

### Project directory structure

```
even-keel/
  firmware/
    boat-mon.yaml
    packages/
      ...
      test_mode.yaml            # compiled only with -D ENABLE_TEST_MODE
  tests/
    conftest.py                 # picks adapter from --mode flag
    requirements.txt
    pytest.ini
    features/
      alerts/...
      telemetry/...
      ais/...
      dashboard/...
      resilience/...
    steps/
      common_steps.py
      alert_steps.py
      dashboard_steps.py
      ais_steps.py
    adapters/
      base.py                   # BoatAdapter protocol
      virtual.py                # Wokwi + MQTT inject
      hil.py                    # serial to HIL ESP32
      live.py                   # MQTT test-mode to deployed firmware
    wokwi/
      diagram.json
      wokwi.toml
      chips/                    # custom Wokwi chip models
    docker/
      compose.yml               # mosquitto + HA
      ha-config/
      mosquitto/
    samples/
      lake_erie_10min.aivdm
      gps_tracks/
        slip_static.nmea
        anchor_drag.nmea
      victron/
        charging.json
        discharging.json
    snapshots/
      kelly_card_dry.png
      kelly_card_bilge_wet.png
  hil-rig/
    README.md
    firmware/                   # secondary ESP32 sketch for HIL stimuli
    bom.md
```

---

## E. Dashboard Simulation and Screenshot Testing

The system has three dashboard surfaces (after the local-dashboard research):

1. **HA Lovelace card on the home tablet (Kelly)** and Pete's full dashboard.
2. **ESPHome `web_server`** on BoatMon-1 (Tier 2 on phones).
3. **LVGL TFT panel** on a dedicated ESP32-S3 at nav station (Tier 1, Phase 10).

Simulation approach per surface:

- **HA Lovelace:** HA in Docker + Playwright. Log in with long-lived token session saved as `storageState.json`. Screenshot individual cards scoped by locator (not full page).
- **ESPHome `web_server`:** Point Playwright at the server (Wokwi in virtual mode, real device in HIL/live). ESPHome's default UI is visually stable.
- **LVGL TFT panel:** LVGL's PC simulator (SDL-based, https://github.com/lvgl/lv_port_pc_eclipse). Render to an offscreen framebuffer via Xvfb, then screenshot. Feed stimuli via a shim that backs the ESPHome data bus from the test harness's MQTT.

### Visual regression approach

- **Don't snapshot whole pages.** Snapshot individual cards by locator. Reduces flakiness.
- **Mask volatile regions** (timestamps, RSSI) — Playwright supports `mask:` on `toHaveScreenshot()`.
- **Dual baselines per theme** (HA light + dark); parametrize with pytest-bdd Scenario Outline.
- **Pin viewport and DPR** (1280×800 @ 2x) to match Kelly's tablet.
- Store baselines in `tests/snapshots/`. Failing diffs upload to GitHub Actions as artifacts for human review.

---

## F. HIL Test Rig (Bench Hardware-in-the-Loop)

Purpose: drive *real physical inputs* into the production ESP32 monitor on a bench, so the same Gherkin that ran in Wokwi runs against actual firmware on the actual board before the boat.

### Architecture

```
[Test runner PC] ──USB──► [HIL ESP32 "stimulator"] ──► [Production ESP32 "BoatMon"]
                                          │
                                          ├── 2-channel relay → shore / genset opto inputs
                                          ├── 2-channel relay → bilge float terminal
                                          ├── MCP4725 DAC → starter-voltage divider input
                                          ├── MCP4725 #2 → INA226 emulation via I2C-slave mode
                                          ├── DS18B20 emulator (OneWireHub on HIL MCU core)
                                          ├── UART out → AIS replay → BoatMon UART1 RX
                                          └── BLE advertiser (HIL ESP32) → Victron frames
```

The HIL ESP32 runs a tiny Arduino/IDF sketch speaking JSON-over-serial: `{"cmd":"bilge","wet":true}`, `{"cmd":"temp","zone":"cabin","c":22.5}`. The `HilAdapter` on the test runner serializes adapter calls onto that port.

### BOM (~$71)

| Item | Use | Est. $ |
|---|---|---|
| ESP32-S3 DevKitC (second unit) | HIL controller | 15 |
| SRD-05VDC 4-channel relay module | bilge / opto switching | 6 |
| MCP4725 12-bit DAC breakout ×2 | analog stimuli | 8 |
| OneWireHub-compatible MCU (RP2040 Zero or second core) | DS18B20 emulation | 4 |
| Perfboard + terminal blocks + headers | wiring | 10 |
| Small plastic project box | tidy rig | 8 |
| Jumper wires, Dupont kits | — | 5 |
| USB-C hub (reach both ESP32s) | — | 12 |
| Misc resistors | — | 3 |
| **Total** | | **~$71** |

Leaves headroom for a small LCD + button to arm/disarm stimuli for safety.

---

## G. Open Questions for Pete

1. **Test-mode security.** Build-flag-gated + HMAC-gated acceptable, or should test mode literally not ship in any production firmware (requires reflash for live-integration)? Recommendation: "shipped but locked."
2. **Wokwi license.** CI minutes free for public repos. If private, budget ~$12–30/mo (would violate no-subscription rule) or run Wokwi on a self-hosted runner.
3. **Acceptable clock-time.** Many scenarios use real-time waits. Add time-acceleration (HA `simulated_time` + firmware debounce overrides)? Recommendation: keep real time for critical alerts, shorten debounces via test-mode overrides for everything else.
4. **Relay service coverage.** Include the AIS-forward service in EvenKeel's test suite (docker-compose an aisstream mock), or separate repo with own tests? Recommendation: include — most valuable end-to-end test.
5. **Kelly as stakeholder.** How formal should "non-programmer reads the tests" be? Auto-generated HTML "what the boat is tested for" report is ~30 min of setup.
6. **HIL rig scope.** Genuinely useful, $70 and a weekend. Defer until after Phase 3 when physical ESP32 design is stable.
7. **Victron BLE bindkey in tests.** Real bindkeys shouldn't sit in the test repo. Use per-test bindkey; rebuild firmware for tests with dummy bindkey if runtime override not possible.
8. **TLS in virtual mode.** Real TLS path (self-signed cert) or plaintext? Recommendation: one dedicated `@tls` scenario runs TLS; everything else plaintext in virtual; HIL and live always real TLS.
9. **aisstream.io contributor test account.** Don't use Pete's real key in CI. Mock endpoint or separate test account.
10. **On-boat LVGL panel tests.** The local-dashboard design adds an LVGL Tier 1 panel. Requires LVGL SDL simulator + ShimmedESPHome data bus. Worth adding to the harness from day one, or defer until Phase 10?

---

## Key references
- pytest-bdd: https://github.com/pytest-dev/pytest-bdd
- Wokwi CLI: https://github.com/wokwi/wokwi-cli ; CI action: https://github.com/wokwi/wokwi-ci-action
- ESPHome-Wokwi integration: https://github.com/luar123/esphome-wokwi-integration
- aiomqtt: https://github.com/empicano/aiomqtt
- pyais: https://github.com/M0r13n/pyais
- gpsd/gpsfake: https://gitlab.com/gpsd/gpsd
- Fabian-Schmidt Victron BLE: https://github.com/Fabian-Schmidt/esphome-victron_ble
- tube0013 stream_server: https://github.com/tube0013/esphome-stream-server-v2
- OneWireHub (DS18B20 emulation): https://github.com/orgua/OneWireHub
- Playwright Python: https://github.com/microsoft/playwright-python
- LVGL PC simulator: https://github.com/lvgl/lv_port_pc_eclipse
- pytest-homeassistant-custom-component: https://github.com/MatthewFlamm/pytest-homeassistant-custom-component
