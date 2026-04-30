# tests/wokwi

Headless ESP32-S3 firmware tests that run under [Wokwi CI](https://docs.wokwi.com/wokwi-ci/getting-started).

## What runs here

- **Smoke test** (this directory): boot the BoatMon-1 firmware, assert
  `BoatMon-1 booted` appears on serial within 90 s, fail on
  `Guru Meditation Error`.
- **Scenario tests** (added in Iteration 2D): pytest-bdd Gherkin
  features driving the firmware through Wokwi's serial + virtual
  network, e.g. bilge water → MQTT publication → HA template sensor
  flips to critical.

## Files

- `wokwi.toml` — points the simulator at the ESPHome build artifact
  (`.esphome/build/boatmon-1/.pioenvs/boatmon-1/firmware.factory.bin`).
- `diagram.json` — minimal ESP32-S3-DevKitC-1 with serial monitor
  attached. Add components (DS18B20 1-wire bus, INA226 I²C, etc.) as
  the firmware grows.

## Running locally

You need a Wokwi account and CLI token (free for public repos):

```bash
# Build the firmware
cd firmware
cp secrets.yaml.example secrets.yaml  # or use your real values
esphome compile boat-mon.yaml

# Simulate (from repo root)
export WOKWI_CLI_TOKEN=...
wokwi-cli tests/wokwi --timeout 90000 \
  --expect-text "BoatMon-1 booted" \
  --fail-text "Guru Meditation Error"
```

GitHub Actions runs the same flow on every change to `firmware/**`,
`tests/wokwi/**`, or the workflow itself — see
`.github/workflows/wokwi.yml`.
