# Sailboat Monitor & AIS Gateway — Continuation Brief

*For pasting into the sailboat project to continue this work in a fresh conversation.*

---

## Project context

Pete is designing a single-ESP32 boat monitoring system for his (pending) Hunter 41DS sailboat at Safe Harbor Sandusky on Lake Erie. The system has two roles:

1. **AIS gateway** — receive AIS via a Wegmatt dAISy HAT, expose locally over TCP, and forward to aisstream.io so Pete's (to-be-built) mobile tracking app and Kelly can see the boat's position.
2. **Boat telemetry** — monitor batteries, temperatures, bilge, shore/generator/battery power source, and (in later phases) GPS, tank levels, anchor drag. Publish via MQTT-over-TLS to Home Assistant at home. Kelly uses a minimal "How's My Boat" dashboard card on a home tablet.

A full architectural design document was produced: **`sailboat-monitor-design.md`**. Treat that as the source of truth.

---

## Key decisions already locked

| Decision | Choice |
|---|---|
| MCU | ESP32-S3-DevKitC-1-N16R8V (final). M5Atom for bench only. |
| Framework | ESPHome, with external components for stream_server and victron_ble |
| AIS receiver | Wegmatt dAISy HAT, wired via breakout pads (no Pi) |
| Enclosure | Commercial dry box — Polycase WC-23F or Bud NBB-15242 |
| Breakout | CZH-Labs or DIYables screw-terminal adapter for 38-pin ESP32 |
| Connectors | Screw terminals inside; M12 A-coded bulkheads for external sensor runs |
| Power input | 12V house bank → fuse → TVS → buck → USB-C pass-through power bank → ESP32 |
| UPS | USB-C power bank with confirmed simultaneous charge/discharge (Voltaic V50 primary candidate) |
| UPS runtime | 12h minimum; expected 20h+ with Voltaic V50 |
| Cloud | Oracle Cloud Always Free — ARM A1.Flex VMs |
| MQTT broker | Mosquitto on OCI with Let's Encrypt TLS |
| HA integration | Stock MQTT integration, no customizations |
| AIS forwarding | Python relay on OCI, pulls ESP32 TCP via WireGuard tunnel, pushes to aisstream.io contributor feed |
| Networking | Multi-SSID WiFi priority (onboard LTE router primary; marina WiFi secondary if PSK-capable) |
| OTA | Via WireGuard tunnel: home → OCI → onboard router → ESP32 |
| Router | Pete's existing 4×4 MIMO X75 cellular router |
| Stretch — HA AIS relay | Second relay at home for active/active redundancy |
| Stretch — HA MQTT broker | Mosquitto bridge at home reading from OCI |

## Scope decisions

**In for v1 (Phases 1–6):**
- AIS reception + TCP stream + OCI relay to aisstream
- MQTT telemetry to OCI broker + HA
- 3 temp zones (cabin / engine compartment / fridge)
- House + starter battery voltages
- Shore / generator / battery power source detection
- Binary bilge (float switch)
- Kelly's "How's My Boat" HA card
- Push/TTS/email alerts for bilge, low battery, offline, shore lost

**Phases 7–10 (post-soak):**
- Victron SmartShunt BLE (Phase 7)
- GPS + tank levels (Phase 8)
- Anchor drag / slip breakaway (Phase 9)
- 10 temp zones + full Pete dashboard (Phase 10)

**Out of scope for v1, explicit future:**
- Remote actuation (bilge blower, cabin fan, heater) — noted as v2
- NMEA 2000 bridge
- Chartplotter server role
- Engine RPM via alternator W

## Open questions to resolve in this project

1. Does the purchased Hunter 41DS have an AIS transponder? If not, plan Class B+ SOTDMA (Vesper Cortex V1 or em-trak B954 — connect to marine electrical upgrade plan).
2. AIS antenna strategy on the Hunter: splitter off existing VHF vs dedicated AIS antenna. Decide at mast/rigging inspection.
3. Victron SmartShunt installation timing vs. Phase 7 start.
4. Onboard LTE router: document WireGuard server config, admin credentials, static DHCP lease for ESP32.
5. Home WireGuard setup to OCI peer — document topology.
6. Tank sender resistance standard on the Hunter 41DS (likely US 240–33Ω; verify at purchase).
7. Safe Harbor Sandusky WiFi — PSK or captive portal? Test at first slip visit.
8. MQTT topic naming convention: settle `boat/hunter41/...` vs `boat/<mmsi>/...` before deployment.
9. Dedicated TLS sub-domain for MQTT.
10. Final pass-through power bank part number after bench verification.

## Prior-art references used

- [open-boat-projects.org](https://open-boat-projects.org/en/) — NMEA patterns, tank/alternator-W patterns
- [Bareboat Necessities](https://bareboat-necessities.github.io/) — marine sensor catalog, XDR patterns
- [Fabian-Schmidt/esphome-victron_ble](https://github.com/Fabian-Schmidt/esphome-victron_ble) — Phase 7
- [tube0013/esphome-stream-server-v2](https://github.com/tube0013/esphome-stream-server-v2) — AIS TCP bridge
- [NauticApp/BilgeMonitor](https://github.com/NauticApp/BilgeMonitor) — ultrasonic bilge (stretch phase)
- [Practical Boat Owner smart engine monitor](https://www.pbo.co.uk/expert-advice/how-i-installed-a-smart-engine-monitoring-system-on-my-sailboat-97830) — single-ESP32 pattern
- [Wegmatt dAISy HAT manual](http://www.wegmatt.com/files/dAISy%20HAT%20AIS%20Receiver%20Manual.pdf) — breakout pad usage
- [aisstream.io documentation](https://aisstream.io/documentation) — contributor API target
- [L-36 DIY ESP32](https://l-36.com/DIY-ESP32) — quiescent current notes

## Suggested prompt to continue in the sailboat project

> Load the `sailboat-monitor-design.md` document. We're ready to start Phase 1: bench prototype. My bench hardware is the M5Atom ESP32 I already own. Walk me through:
>
> 1. Wiring the dAISy HAT to the M5Atom via breakout pads (which pads, which Atom pins).
> 2. A minimal ESPHome YAML that runs `stream_server` on :6638 with just WiFi + OTA + logger — no MQTT yet.
> 3. How to verify AIS is being received and served via telnet/OpenCPN.
>
> Also: recommend the VHF whip antenna I should use for bench testing (Lake Erie traffic visibility from Orrville is zero, so this will need a better antenna or a setup at the marina. What's the cheapest way to bench-test?).

## Conversation export

The full conversation preceding this document is saved in the thread this was produced from. To export the conversation verbatim, use the share/export function in Claude.ai. The design decisions and tradeoffs captured in `sailboat-monitor-design.md` are the essential artifacts — the conversation transcript is supplementary context.

---

*End of continuation brief.*
