# firmware/

ESPHome YAML configurations for EvenKeel devices.

## Devices

- **`boat-mon.yaml`** — BoatMon-1: the primary ESP32-S3 on the boat. AIS RX, sensors, Tier 0 LED/buzzer, Tier 2 `web_server` dashboard. (Phases 1-9)
- **`dashboard-head.yaml`** — DashboardHead-1: the nav-station LVGL panel on a Waveshare ESP32-S3-Touch-LCD-4.3. (Phase 10)

## Structure

```
firmware/
  boat-mon.yaml           # main device config
  dashboard-head.yaml     # Phase 10 LVGL panel
  secrets.yaml.example    # template; real secrets.yaml is gitignored
  packages/
    base.yaml             # logger, api, ota, wifi, fallback AP
    network.yaml          # MQTT client + LWT
    ais.yaml              # uart + stream_server
    temperature.yaml      # 1-wire bus + per-zone sensors
    power.yaml            # INA226, voltage divider, opto-isolators
    bilge.yaml            # float switch + Tier 0 buzzer GPIO
    health.yaml           # RSSI, uptime, free heap, IP
    victron.yaml          # (Phase 7) BLE components
    gps.yaml              # (Phase 8) uart2 + GPS
    tanks.yaml            # (Phase 8) ADS1115 + calibration
    test_mode.yaml        # MQTT-gated injection; compiled only with -D ENABLE_TEST_MODE
```

## Building

```bash
esphome compile boat-mon.yaml             # production build
esphome compile boat-mon.yaml -DENABLE_TEST_MODE   # test-mode build
```

## OTA

Only reachable from boat LAN or via WireGuard tunnel from home. Password-protected and encrypted.
