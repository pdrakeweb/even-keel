# HIL Rig — Bill of Materials

Total: **~$71**.

| Item | Use | Source | Est. $ |
|---|---|---|---|
| ESP32-S3 DevKitC-1 (second unit) | HIL controller | Digi-Key / Adafruit | 15 |
| SRD-05VDC 4-channel relay module | bilge / shore-opto / gen-opto switching | Amazon | 6 |
| MCP4725 12-bit DAC breakout × 2 | analog stimuli (battery dividers) | Adafruit | 8 |
| OneWireHub-capable MCU (RP2040 Zero or second core of HIL ESP32) | DS18B20 emulation | Adafruit | 4 |
| Perfboard + terminal blocks + headers | wiring | Adafruit | 10 |
| Small plastic project box | enclosure | Hammond 1591B | 8 |
| Jumper wires + Dupont kits | — | Amazon | 5 |
| USB-C hub (reach both ESP32s from test PC) | — | Amazon | 12 |
| Misc resistors + arm/disarm button + LED | — | Amazon | 3 |
| **Total** | | | **~$71** |

Options (not included in base cost):

- 16×2 character LCD for status display: +$8
- Second ESP32-S3 for BLE Victron advertiser (Phase 7 testing): +$15
