# hil-rig/

Hardware-in-the-loop bench rig for EvenKeel. Drives real physical stimuli into a production BoatMon-1 unit so Gherkin scenarios that run in Wokwi also run against the actual firmware on the actual board before the boat.

See [`../planning/tdd-architecture.md §F`](../planning/tdd-architecture.md) for the architecture.

## BOM (~$71)

See `bom.md`.

## Build

Secondary ESP32-S3 runs `firmware/hil-stimulator.ino` (or ESPHome) exposing a JSON-over-serial protocol. Test runner serializes `BoatAdapter` calls to the port.

```
{"cmd": "bilge", "wet": true}
{"cmd": "temp", "zone": "cabin", "c": 22.5}
{"cmd": "voltage", "bank": "house", "v": 12.3}
{"cmd": "ais_replay", "file": "samples/lake_erie_10min.aivdm"}
```

## Safety

A physical arm/disarm button on the rig gates all relay outputs — stimuli cannot fire when the rig is disarmed. LCD shows the current stimulus and the "armed" state.
