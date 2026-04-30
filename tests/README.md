# tests/

Natural-language test harness for EvenKeel. See [`../planning/tdd-architecture.md`](../planning/tdd-architecture.md) for the full design.

## Running locally

The harness needs a Mosquitto broker. Use the repo's `docker compose`
stack — the same one used for UI dev.

```bash
# From the repo root:
docker compose up -d mosquitto

# Then from tests/:
pip install -e ../simulator     # provides evenkeel_sim for the adapter
pip install -r requirements.txt
pytest -v
```

Pick a different mode or a tag subset:

```bash
pytest --mode=virtual                        # default — simulator + local MQTT
pytest --mode=hil --hil-port=/dev/ttyUSB0    # bench HIL rig (Phase 4+)
pytest --mode=live --broker=boat-broker.peteskrake.com  # deployed firmware

pytest -m phase1                             # one phase at a time
pytest -m "alerts and not ble"               # tag expressions
pytest -m "telemetry and critical"           # smoke subset
```

CI runs the virtual-mode suite on every push touching `tests/**` or
`simulator/**` — see `.github/workflows/integration-tests.yml`.

## Status

**36 tests green in CI** (Linux runner, Mosquitto + Chromium service containers):

- 23 Gherkin scenarios across 7 feature files (bilge, battery, engine,
  leak, AIS targets, anchor watch — all under `features/telemetry/` and
  `features/ais/`)
- 7 `SimulatorPublisher` integration tests that spin up the real
  simulator publish loop and assert on what lands on MQTT
- 6 Playwright e2e tests against the production custom-card bundle in
  real Chromium (skipped on Windows; CI Linux runs them)

Three-mode adapter harness is structurally complete — see
[`adapters/README.md`](adapters/README.md). Currently only `--mode=virtual`
runs end-to-end; HIL and live skeletons raise `NotImplementedError` at
startup until Phase 4 / Phase 6 commissioning.

The aspirational `features/alerts/bilge_alarm.feature` covers the full
Phase 6 notification path (HA REST + Pushover + Sonos). It's unbound
to a `test_*.py` until the HA REST adapter lands.

## Layout

```
tests/
  conftest.py                 # --mode flag wires the correct adapter
  requirements.txt
  pytest.ini
  features/                   # Gherkin .feature files, organized by capability
    alerts/
    telemetry/
    ais/
    dashboard/
    resilience/
  steps/                      # step implementations shared across modes
    common_steps.py
    alert_steps.py
    dashboard_steps.py
    ais_steps.py
  adapters/
    base.py                   # BoatAdapter protocol
    virtual.py                # Wokwi + Docker MQTT
    hil.py                    # serial to HIL ESP32
    live.py                   # MQTT test-mode to deployed firmware
  wokwi/
    diagram.json
    wokwi.toml
    chips/
  docker/
    compose.yml               # mosquitto + HA
    ha-config/                # minimal HA for tests
    mosquitto/
  samples/                    # replayable test data
    lake_erie_10min.aivdm
    gps_tracks/
    victron/
  snapshots/                  # Playwright visual regression baselines
```

## Writing new scenarios

Each `.feature` file covers one user-visible capability. Example:

```gherkin
# features/alerts/bilge_alarm.feature
Feature: Bilge water alarm

  @phase6 @critical
  Scenario: Bilge float switch triggers a notification
    Given the boat monitoring system is online
    When the bilge float switch reports water for 10 seconds
    Then within 30 seconds Pete should receive a push notification containing "WATER DETECTED"
```

Step definitions live in `steps/` and call the `boat` fixture (a `BoatAdapter`). Never reference the adapter directly in steps — the harness selects virtual/HIL/live based on `--mode`.
