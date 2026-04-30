# tests/adapters

The single seam between Gherkin step definitions and the world.

Step definitions in `tests/steps/` call methods on the abstract
`BoatAdapter` Protocol — they never know which concrete adapter is
wired in. The test runner picks one based on `--mode`:

| Mode      | Adapter                           | "Boat" is…                                   | Status                  |
|-----------|-----------------------------------|----------------------------------------------|-------------------------|
| `virtual` | [`VirtualAdapter`](virtual.py)    | EvenKeel simulator + local Mosquitto         | Implemented + tested in CI |
| `hil`     | [`HilAdapter`](hil.py)            | Bench-rig ESP32-S3 (`hil-rig/`) over USB serial | Skeleton — Phase 4 commissioning |
| `live`    | [`LiveIntegrationAdapter`](live.py) | Deployed boat firmware via MQTT test/* topics | Skeleton — Phase 6 HMAC handshake |

See [`../../planning/tdd-architecture.md`](../../planning/tdd-architecture.md)
§C for the original layered design and the security model behind the
live-mode test_mode injection.

## The contract

[`base.py`](base.py) declares the Protocol every adapter implements.
Stimulus methods (`set_bilge`, `set_engine_running`, …) drive the boat
into a target state. Observation methods (`mqtt_last`, `wait_for`,
`entity_state`, `wait_for_notification`) read back from canonical sources.

The split lets a Gherkin scenario like:

```gherkin
Given the boat is online
When the bilge float switch reports water
Then within 5 seconds MQTT topic "boat/hunter41/bilge/water_detected" equals "1"
```

…drive a simulator (virtual), a bench rig (HIL), or the actual deployed
ESP32 (live) through *the same step definitions*. The same Gherkin file
exercises three layers without rewriting.

## Adding a new stimulus

1. Add the method signature to `base.BoatAdapter` Protocol.
2. Implement it in `virtual.VirtualAdapter` — typically one line that
   calls `self._publish_field("<sensor_field>", value)` or for
   composite cases, multiple field publishes.
3. Mirror it in `live.LiveIntegrationAdapter` to publish to the
   `boat/hunter41/test/<sensor_path>` topic for the firmware's
   test_mode package to consume.
4. Stub it in `hil.HilAdapter` (just the `...` Protocol stub for now).
5. Add the step definition in `tests/steps/*.py` referencing the new
   method.

## Why three modes?

Each catches different bugs:

- **virtual** — fast, deterministic, runs on every push. Catches contract
  drift between simulator and harness.
- **HIL** — slow but real hardware. Catches GPIO timing, opto-isolator
  thresholds, ADC calibration, all the analog reality the simulator
  fakes.
- **live** — runs against the actual boat. Catches deployment-only
  bugs: WiFi radio environment, real Victron BLE adverts, real bilge
  float chatter, real marina power flicker.
