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
esphome compile boat-mon.yaml             # production build (no injection surface)
```

For a dev / test-mode build, copy `boat-mon.yaml` to a sibling that
adds `test_mode: !include packages/test_mode.yaml` to the packages
list. Production binaries should never include `test_mode.yaml` —
see the security model in that file's header.

## OTA

Only reachable from boat LAN or via WireGuard tunnel from home. Password-protected and encrypted.

## CI: Wokwi simulation

The `Wokwi firmware simulation` workflow builds this firmware and
boots it under a headless ESP32-S3 in Wokwi
(`.github/workflows/wokwi.yml`). Wokwi requires a personal CI token,
which the workflow reads from a repository secret.

**One-time setup:** add the token at
`Settings → Secrets and variables → Actions → New repository secret`:

| Name              | Value                                            |
|-------------------|--------------------------------------------------|
| `WOKWI_CLI_TOKEN` | from <https://wokwi.com/dashboard/ci> (free tier covers OSS / public-repo CI) |

Until the secret is set, the simulation step short-circuits with a
clear error and the workflow fails — by design, so a missing secret
isn't silently masked. The local `.env` file (gitignored) is also a
convenient place to keep the token for `wokwi-cli` runs from your
own machine.
