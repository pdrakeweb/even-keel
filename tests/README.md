# tests/

Natural-language test harness for EvenKeel. See [`../planning/tdd-architecture.md`](../planning/tdd-architecture.md) for the full design.

## Running

```bash
pip install -r requirements.txt
docker compose -f docker/compose.yml up -d mosquitto homeassistant

pytest --mode=virtual                        # Wokwi + Docker MQTT/HA
pytest --mode=hil --hil-port=/dev/ttyUSB0    # bench HIL rig
pytest --mode=live --broker=boat-broker.peteskrake.com  # deployed firmware

pytest -m phase5                             # one phase at a time
pytest -m "alerts and not ble"               # tag expressions
```

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
