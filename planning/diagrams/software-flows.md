# EvenKeel — Software Flow Diagrams

Mermaid diagrams covering data flow, state machines, and control flow. Render in GitHub, VS Code (with Mermaid extension), or at https://mermaid.live.

---

## 1. End-to-End Sensor Telemetry Flow

```mermaid
sequenceDiagram
    participant S as Sensor<br/>(e.g., DS18B20)
    participant F as ESP32 firmware<br/>(ESPHome)
    participant BB as Boat Broker<br/>(Mosquitto on Pi)
    participant WG as WireGuard Tunnel
    participant HB as Home Broker<br/>(HA Mosquitto add-on)
    participant HA as Home Assistant
    participant KT as Kelly's Tablet
    participant PP as Pete's Phone

    S->>F: temp reading (1-wire poll every 30s)
    F->>F: apply filters / templates
    F->>BB: publish<br/>boat/hunter41/temp/cabin = 22.4<br/>(QoS 0, TLS)
    BB->>BB: retain last value
    BB->>WG: bridge forwards boat/# topic
    WG->>HB: delivers to home broker
    HB->>HA: MQTT discovery entity update
    HA->>HA: update recorder
    HA->>KT: Lovelace card refresh via WebSocket
    HA->>PP: Companion app state sync
```

---

## 2. AIS Pipeline

```mermaid
flowchart LR
    VHF[VHF/AIS Antenna]
    D[dAISy HAT]
    UART[UART :38400]
    SS[ESPHome<br/>stream_server]
    TCP[TCP :6638 on boat LAN]

    subgraph LocalConsumers["On-boat consumers"]
        OCPN[OpenCPN at nav]
        CP[Existing Chartplotter]
    end

    subgraph HomeConsumers["Home consumers via WG"]
        HACPN[OpenCPN at home]
        Relay[AIS forwarder<br/>HA add-on · OPTIONAL]
    end

    AIS[aisstream.io<br/>contributor feed · OPT-IN]

    VHF --> D --> UART --> SS --> TCP
    TCP --> OCPN
    TCP --> CP
    TCP -.->|WG tunnel| HACPN
    TCP -.->|WG tunnel| Relay
    Relay -.->|opt-in only| AIS

    classDef optional stroke-dasharray: 5 5
    class Relay,AIS optional
```

---

## 3. Three-Layer Alert Delivery (Critical Alerts)

```mermaid
flowchart TD
    Event([Bilge float goes wet<br/>for ≥10 s])

    Event --> ESP[BoatMon-1 firmware]

    ESP --> L1{Layer 1<br/>GPIO-direct}
    L1 --> Buzz[Tier 0:<br/>Buzzer + Red LED<br/>ALWAYS WORKS]

    ESP --> L2{Layer 2<br/>Direct Pushover<br/>over LTE}
    L2 -->|HTTPS POST to<br/>api.pushover.net| Push[Pete's + Kelly's<br/>Pushover app]

    ESP --> L3{Layer 3<br/>MQTT → HA}
    L3 --> MQ[boat/hunter41/bilge/water_detected = 1]
    MQ -->|WG bridge| HA[Home HA]
    HA --> HP[HA Companion push]
    HA --> TTS[Google Cast TTS<br/>on home speakers]
    HA --> EM[SMTP email<br/>Pete's own server]
    HA -.->|opt-in if<br/>user's subscription| SMS[Twilio SMS]

    classDef alwaysOn fill:#ffeeee,stroke:#c00
    class Buzz,Push alwaysOn
    classDef conditional fill:#eeeeff
    class HP,TTS,EM,SMS conditional
```

**Severity routing:**

| Severity | Layers | Examples |
|---|---|---|
| Critical | 1 + 2 + 3 (all three) | Bilge wet, anchor drag, boat offline >15m |
| Warning | 3 only | Low battery, shore power lost at slip, generator started |
| Info | 3 only, quiet hours respected | Daily summary, uptime milestones |

---

## 4. Boot / Recovery State Machine

```mermaid
stateDiagram-v2
    [*] --> Boot
    Boot --> WiFi_Scan: config loaded
    WiFi_Scan --> WiFi_Connected: known SSID found
    WiFi_Scan --> AP_Mode: no known SSID for 5 min
    AP_Mode --> WiFi_Scan: user reconfigures

    WiFi_Connected --> MQTT_Connect
    MQTT_Connect --> MQTT_Connected: TLS handshake OK
    MQTT_Connect --> MQTT_Retry: broker unreachable
    MQTT_Retry --> MQTT_Connect: backoff 5..60s
    MQTT_Retry --> Reboot: 10 failures

    MQTT_Connected --> Running: publish birth<br/>boat/.../status/online=ON

    Running --> Running: publish telemetry<br/>every 30-60s
    Running --> Alert_Active: bilge/anchor/critical event
    Alert_Active --> Running: condition clears

    Running --> WiFi_Lost: WiFi dropout
    WiFi_Lost --> WiFi_Scan: 30s retry
    WiFi_Lost --> Degraded_Local: AIS + Tier 0 continue
    Degraded_Local --> WiFi_Scan: retry loop

    Running --> OTA_Update: push from home HA
    OTA_Update --> Boot: new firmware flashed

    Reboot --> Boot
```

---

## 5. Boat ↔ Home Connectivity States

```mermaid
stateDiagram-v2
    [*] --> Full_Telemetry
    Full_Telemetry: All paths up<br/>MQTT flowing<br/>HA live

    Full_Telemetry --> WG_Down: WireGuard fails
    WG_Down: Boat collects locally<br/>Retained topics build<br/>Home HA shows stale

    WG_Down --> Full_Telemetry: tunnel re-established<br/>retained state replays

    Full_Telemetry --> Boat_Offline: LTE router off
    Boat_Offline: HA marks online=OFF<br/>after 5 min silence<br/>Tier 0 buzzer still active<br/>Phone PWA still works on<br/>BoatMon-Fallback AP

    Boat_Offline --> Full_Telemetry: router back up

    Full_Telemetry --> Home_Offline: home ISP down
    Home_Offline: Boat broker OK<br/>Tier 0 works<br/>Pushover critical path OK<br/>HA dashboard dark

    Home_Offline --> Full_Telemetry: home ISP back

    Full_Telemetry --> ESP_Crashed: firmware/hardware fail
    ESP_Crashed: Bridge LWT fires<br/>HA: online=OFF<br/>Tier 0 silent<br/>Pushover silent<br/>Only defense:<br/>boat's traditional alarms

    ESP_Crashed --> Full_Telemetry: reboot / OTA fix

    note right of Boat_Offline
        Critical invariant:
        Tier 0 (LED+buzzer) fires
        regardless of any
        network connectivity.
    end note
```

---

## 6. OTA Firmware Update Flow

```mermaid
sequenceDiagram
    participant PL as Pete's Laptop
    participant HR as Home Router<br/>(WG server)
    participant LT as Boat LTE Router<br/>(WG client)
    participant HA as Home HA ESPHome
    participant BM as BoatMon-1 ESP32

    PL->>HR: WG handshake (Pete's phone/laptop key)
    HR-->>LT: (tunnel already established,<br/>keepalive)
    PL->>HA: open ESPHome dashboard @ home-ha.local
    PL->>HA: "Install" for boat-mon.yaml
    HA->>HA: compile firmware.bin
    HA->>LT: HTTP push to<br/>boatmon-1.boat.int:3232 via WG
    LT->>BM: forward to boat LAN
    BM->>BM: verify OTA password/key
    BM->>BM: flash, verify, reboot
    BM->>HA: re-publish birth message
    PL->>PL: see "Online" in ESPHome UI
```

---

## 7. Test Harness Adapter Selection

```mermaid
flowchart TD
    pytest["pytest --mode=X"]
    conftest[conftest.py]
    adapter[BoatAdapter<br/>protocol]

    pytest -->|parses CLI flag| conftest
    conftest -->|picks one| adapter

    adapter --> VA[VirtualAdapter]
    adapter --> HA_ad[HilAdapter]
    adapter --> LA[LiveIntegrationAdapter]

    subgraph Virtual["--mode=virtual (CI default)"]
        VA --> Wokwi[Wokwi CLI<br/>ESP32-S3 sim]
        VA --> DockerMQ[docker-compose:<br/>mosquitto]
        VA --> DockerHA[docker-compose:<br/>Home Assistant]
    end

    subgraph HIL["--mode=hil (bench, tagged releases)"]
        HA_ad --> Serial[JSON-over-serial<br/>to HIL ESP32]
        Serial --> Stimulator[Stimulator ESP32<br/>+ relays + DACs]
        Stimulator --> RealBM[Real BoatMon-1<br/>on the bench]
    end

    subgraph Live["--mode=live (deployed, sparingly)"]
        LA --> MQTTi[MQTT inject to<br/>boat/hunter41/test/*<br/>HMAC-gated]
        MQTTi --> Deployed[Deployed BoatMon-1<br/>on the actual boat]
    end

    VA --> Steps[Same Gherkin<br/>step definitions]
    HA_ad --> Steps
    LA --> Steps
```

---

## 8. Test-Mode Injection Gating (firmware)

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Normal

    Normal: Real sensor values published<br/>test_mode_active = false
    Normal --> Enable_Pending: receive retained<br/>boat/hunter41/test/enable

    Enable_Pending: verify HMAC against<br/>secrets.yaml shared key
    Enable_Pending --> Normal: HMAC invalid → audit-log + ignore
    Enable_Pending --> Test_Active: HMAC valid

    Test_Active: publish "TEST MODE" retained<br/>HA fires "Boat in test mode" alert<br/>Accept boat/hunter41/test/<sensor> injections<br/>Audit every injection

    Test_Active --> Keepalive_Check: every 60s
    Keepalive_Check --> Test_Active: keepalive received<br/>within last 10 min
    Keepalive_Check --> Normal: no keepalive 10+ min<br/>auto-disable<br/>audit-log exit

    Test_Active --> Normal: receive enable=OFF<br/>(HMAC-signed)
```

---

## 9. Firmware Module Graph (ESPHome Packages)

```mermaid
flowchart LR
    Main[boat-mon.yaml<br/>main config]

    Main --> Base[packages/base.yaml<br/>logger, api, ota, wifi]
    Main --> Net[packages/network.yaml<br/>mqtt + LWT + birth]
    Main --> AIS[packages/ais.yaml<br/>uart + stream_server]
    Main --> Temp[packages/temperature.yaml<br/>1-wire + DS18B20s]
    Main --> Pwr[packages/power.yaml<br/>INA226, divider, optos]
    Main --> Bilge[packages/bilge.yaml<br/>float + Tier 0 GPIO]
    Main --> Health[packages/health.yaml<br/>rssi, uptime, heap]
    Main --> Alerts[packages/alerts.yaml<br/>Pushover HTTP direct]
    Main -.->|Phase 7| Vic[packages/victron.yaml<br/>BLE advertisements]
    Main -.->|Phase 8| GPS[packages/gps.yaml<br/>uart2 + gps]
    Main -.->|Phase 8| Tanks[packages/tanks.yaml<br/>ADS1115 + calibration]
    Main -.->|-D ENABLE_TEST_MODE| TM[packages/test_mode.yaml<br/>HMAC-gated injection]

    classDef opt stroke-dasharray: 5 5
    class Vic,GPS,Tanks,TM opt
```

---

## 10. A Day in the Life (narrative)

```mermaid
gantt
    title A Day on the Hunter 41DS
    dateFormat  HH:mm
    axisFormat  %H:%M

    section Boat
    House bank discharge (refrigerator cycling)           :a1, 00:00, 24h
    Telemetry publishes every 60s                         :a2, 00:00, 24h
    AIS targets in range (background chatter)             :a3, 00:00, 24h

    section Event
    Engine start (voltage dip 11.1V transient)            :crit, 09:00, 2m
    Generator on                                          :active, 09:00, 1h
    Shore power disconnect (departing slip)               :milestone, 09:15, 0
    Underway - AIS targets update frequently              :09:15, 6h
    Anchor set                                            :milestone, 15:15, 0
    Anchor mode armed in HA                               :15:15, 10m
    Sunset - night mode toggled on Tier 1 panel (future)  :milestone, 20:30, 0

    section Alerts fired
    Generator-started info push to Pete                   :milestone, 09:00, 0
    Shore-lost warning push                               :milestone, 09:15, 0
    Anchor-armed confirmation                             :milestone, 15:15, 0
```
