# EvenKeel — Open Questions

**Status:** The Top 10 blocking questions have been resolved with Pete (see §0). Remaining items are post-v1 or implementation-time decisions.

**Legend:**
- ✅ **Resolved** (Pete decided)
- 🔴 **Blocks Phase 1** (answer before starting)
- 🟡 **Blocks Phase 2–6** (answer before v1 ship)
- 🟢 **Can defer to post-v1**

---

## 0. Resolved Decisions (Pete, April 2026)

These supersede the recommendations below for matching question IDs.

| # | Question | Decision |
|---|---|---|
| **Q1** | Home ISP CGNAT | UDP port-forward is available. Home router will expose UDP :51820 for WireGuard with appropriate hardening (see `infrastructure.md §WG Security`). |
| **Q1b** | Home router as dependency | **NEW CONSTRAINT:** EvenKeel must not require the home router to be reachable. Home router is the *convenience* path for remote access and the *default* alert-delivery path via HA — but the core boat application (local dashboards, Tier 0 buzzer, on-boat alerts) must run indifferent to home reachability. Design implication: add a **direct-from-boat critical-alert path** (Pushover — one-time $5, no subscription) so bilge/anchor/critical alerts reach Pete's phone even when home HA is offline. |
| **Q2** | Boat LTE WG client | (Implicit — deferred; home is WG server, boat is client when tunnel is desired.) |
| **Q6** | UPS / power path | **Simplified: standard USB-C PD.** Optional pass-through power bank (Anker 733 GaNPrime PowerCore — true pass-through, 10Ah, ~$110) for users who want battery backup. NF-3 (12+ h UPS) becomes an *optional* feature rather than a core requirement. Path A (pass-through bank) and Path B (LiFePO4) are both dropped from the base plan. |
| **Q7** | SmartShunt timing | (Question meant: is a Victron SmartShunt being installed separately so we can skip INA226?) **Decision:** Plan INA226 in Phase 5 regardless. Phase 7 layers Victron BLE on top if/when a SmartShunt is installed; HA prefers Victron data when available. |
| **Q16** | AIS transponder on the boat | **Already installed.** AIS BOM line-item for transponder is removed. |
| **Q18** | On-boat LVGL Tier 1 panel in v1 | **Deferred to late phase (Phase 10+).** v1 ships with Tier 0 LED+buzzer + Tier 2 phone PWA only. |
| **Q24** | Test-mode in production firmware | **Ship in production** with HMAC gating + auto-expiry. |
| **Q25/Q39** | Public repo | **Public.** Unlocks free Wokwi CI + GitHub Actions. Secrets management must be bulletproof before first push. |
| **Q26** | aisstream test credentials | **Mock endpoint preferred**; dedicated test account as fallback if mocking proves complex. |
| **Q30** | Alert channels | **HA Companion push = default.** **Twilio SMS = opt-in plugin** for users who already have a Twilio subscription (not a project requirement). **Pushover added as direct-from-boat path** (one-time fee, no subscription) so critical alerts work when HA is unreachable. |

Changes to BOM/phasing flowing from these decisions:
- Phase 3 power design simplified (no bench-verify of pass-through bank; no LiFePO4 drop-in). v1 cost drops.
- Phase 3 gains a direct-from-boat Pushover integration (ESPHome `http_request` POST to Pushover API).
- Phase 10 shrinks (LVGL panel moves to Phase 11+ optional).
- Relay/aisstream path tests use a mock endpoint from day one.

---

---

## A. Infrastructure & Networking

### Q1 🔴 Home ISP CGNAT status
Does Pete's home ISP currently give a routable public IPv4 (can we forward UDP :51820), or is it CGNAT'd?
- **Recommended:** Confirm; if CGNAT, pivot to Cloudflare Tunnel as the inbound path.

### Q2 🔴 Boat LTE CGNAT / IPv6
Does the onboard X75 LTE router get routable IPv6 or a static IPv4? Does it support WireGuard as a **client** with `PersistentKeepalive`?
- **Recommended:** The design assumes **boat is WG client, home is WG server** — CGNAT-safe. Just verify the X75 firmware supports WG client mode.

### Q3 🟡 "Boat asleep" off-season behavior
When the LTE router is off for winter storage, no telemetry reaches home. Acceptable, or do we want a low-power always-on broker?
- **Recommended:** Accept "offline" in winter; revisit only if Kelly explicitly wants mid-winter hull-temp monitoring.

### Q4 🟢 AIS contribution default
Opt-in from Phase 2, or postponed until v1 is stable (Phase 6+)?
- **Recommended:** Postpone until after Phase 6 soak. Not critical for v1.

### Q5 🟢 Remote phone access
WireGuard-only, or add Cloudflare Tunnel from the start for Pete's phone at work?
- **Recommended:** Start WireGuard-only. Add Cloudflare Tunnel in Phase 10 if UX friction is real.

---

## B. Hardware — Power & Core

### Q6 🔴 UPS path: Path A vs Path B
Path A = USB-C pass-through power bank (~$60, 12-30 h runtime, needs bench-verified pass-through). Path B = 10 Ah LiFePO4 drop-in + 12V→5V buck (~$111, 48+ h runtime, marine-native chemistry).
- **Recommended:** **Path B (LiFePO4).** +$51 buys reliability and thermal margin; matches how the rest of the boat is electrified. Defers the risky "does this specific bank actually pass through?" bench exercise.

### Q7 🔴 Victron SmartShunt timing vs. Phase 7
Is a SmartShunt being installed as part of the boat's electrical upgrade? If yes, skip INA226 on house bank. If not, INA226 bridges until Phase 7.
- **Recommended:** Plan for INA226 in Phase 5 regardless; SmartShunt replaces it opportunistically when installed.

### Q8 🟡 Actuator scope in v1
Bilge blower, cabin fan, diesel-heater enable. Safety interlocks, mechanical kill switch, cable runs. Is this v1 or v1.5?
- **Recommended:** **v1.5.** Ship v1 without actuators; add in Phase 11+ as a self-contained sub-phase with its own safety review.

### Q9 🟡 Heater scope
Diesel forced-air (Webasto/Espar) behind interlocks is acceptable. AC resistive space heater is not — fire risk, unprotected.
- **Recommended:** Only diesel-heater enable-line actuation in v1.5. Explicitly refuse AC resistive heater automation.

### Q10 🟢 Connector philosophy
M12 A-coded everywhere (uniform), or M12 for signal + Deutsch DT for actuator outputs (marine-grade, +$50, one more crimper)?
- **Recommended:** M12 everywhere in v1; revisit if actuator package lands.

### Q11 🟢 Spare hardware
Buy 2× dAISy HAT, 2× Polycase WC-23F, 2× ESP32-S3 DevKitC-1 up front? Adds ~$130.
- **Recommended:** Yes for ESP32 (cheap). dAISy — buy one spare. Enclosure — buy one spare.

---

## C. Hardware — Sensors & Install

### Q12 🟡 AIS antenna strategy
Splitter off existing VHF vs. dedicated AIS antenna. Decide at mast/rigging inspection.
- **Recommended:** Start with a dedicated AIS antenna if there's space; no receive-path compromise to VHF.

### Q13 🟡 Tank sender protocol
Hunter 41DS likely US standard (240–33 Ω). Verify at purchase/survey before calibrating.
- **Recommended:** Confirm at survey; if European (10–180 Ω), redo the calibration lookup table.

### Q14 🟡 Engine oil-pressure switch polarity
Most diesel engines close-to-ground when LOW pressure (inverted). Confirm at survey before firmware runtime counter logic.
- **Recommended:** Confirm at survey; write the YAML conditional based on actual wiring.

### Q15 🟢 CO alarm integration
Is a Fireboy-Xintex or equivalent already on the Hunter? If yes, wire its dry-contact output ($0). If not, $90 new unit.
- **Recommended:** Confirm at purchase; buy one if absent — $90 for CO safety is a trivial add.

### Q16 🟢 Does the boat have an AIS transponder?
If not, budget Class B+ SOTDMA (Vesper Cortex V1, em-trak B954) ~$900–1,500. Reception-only means no one tracks *you*.
- **Recommended:** Confirm at purchase; v1 works either way. Plan transponder as a separate purchase, not part of EvenKeel BOM.

### Q17 🟢 Marina WiFi
Safe Harbor Sandusky — PSK-authenticated or captive portal?
- **Recommended:** Test at first slip visit. If captive, ignore and rely on LTE.

---

## D. Local Dashboard

### Q18 🟡 On-boat Tier 1 LVGL panel — in v1 or defer?
Phase 10 by default. Do we want it earlier, or does v1 ship with only Tier 0 LED+buzzer + Tier 2 phone dashboard?
- **Recommended:** **Defer to Phase 10.** Ship v1 with Tier 0 + Tier 2 only. After one sailing season Pete knows what crew actually checks; build Tier 1 then.

### Q19 🟢 Tier 0 buzzer placement
Nav station only or also at helm?
- **Recommended:** Both if cable run is reasonable; helm placement is where the crew actually is.

### Q20 🟢 Tier 1 data source
Direct MQTT to broker, or native-API to BoatMon-1? Native-API + MQTT fallback is cleaner.
- **Recommended:** Native-API primary, MQTT fallback.

### Q21 🟢 Night/red-mode trigger
Manual GPIO button, HA sun-based automation, or both?
- **Recommended:** Manual button for Tier 1 panel; HA sun automation for Kelly's card. Red-mode only applies to the on-boat panel.

### Q22 🟢 LVGL panel display choice
Waveshare 4.3" (350-nit, $45) vs 5" ($55) vs 7" ($75). Smaller = cheaper + less power; larger = more glance-able at distance.
- **Recommended:** 4.3" for v1 Tier 1; verify font-size prototype before cutting mount.

### Q23 🟢 Kelly card location
Home kitchen tablet only, or also phone lock-screen widget?
- **Recommended:** Kitchen tablet only in v1. HA Companion widget is a nice-to-have.

---

## E. Testing & TDD

### Q24 🟡 Test-mode security posture
Build-flag + HMAC-gated test-mode shipped in production firmware, or only in separate test builds (requires reflash for live-integration)?
- **Recommended:** **Ship test-mode in production firmware, HMAC-gated + auto-expiring.** Reflashing a deployed boat ESP32 for testing is operationally expensive.

### Q25 🟡 Wokwi license for CI
Free for public repos. If private, costs ~$12–30/mo (would violate no-subscription rule).
- **Recommended:** **Public repo** for CI. EvenKeel is a DIY project; public is the norm and unlocks free Wokwi + GitHub Actions minutes. If Pete wants private, self-hosted GH Actions runner + local Wokwi.

### Q26 🟡 aisstream test credentials
Don't put Pete's real contributor key in CI. Mock endpoint or a separate test account?
- **Recommended:** Mock endpoint in CI (a tiny FastAPI server that records what the forwarder sends). Real contributor key lives only on home HA host.

### Q27 🟢 Time-acceleration in tests
Many scenarios use real-time waits (5 minutes). Add time-acceleration via HA `simulated_time` + firmware debounce overrides?
- **Recommended:** Keep real-time for critical alerts (p95 latency budget is a real test target). Shorten non-critical debounces via test-mode overrides.

### Q28 🟢 HIL rig timing
$70 bench rig; defer until Phase 3 when physical ESP32 design is stable.
- **Recommended:** **Defer to Phase 3 exit.** Phase 1–2 run virtual-only.

### Q29 🟢 LVGL panel test-harness coverage
Add LVGL SDL simulator + shim now, or defer until Phase 10?
- **Recommended:** Defer until Phase 10. Current tests cover the data layer; visual testing of the panel follows its hardware delivery.

---

## F. Alerts & UX

### Q30 🔴 Alert channels inventory
HA Companion push + TTS on home speakers + email (Pete's own SMTP) — is that sufficient, or is SMS required as fallback?
- **Recommended:** **Push + TTS + email only.** SMS requires Twilio/similar = subscription = forbidden.

### Q31 🟡 Kelly threshold authority
Should Kelly be able to tune green/amber thresholds on her card via `input_number` helpers?
- **Recommended:** **Pete owns thresholds** in v1; exposes them only if Kelly explicitly wants tuning.

### Q32 🟡 Offline-alert routing
When boatmon is offline 15 min, notify Pete only (avoid alarming Kelly for mundane WiFi hiccups). Confirm?
- **Recommended:** **Confirm.** Pete gets offline alert; Kelly gets bilge/battery/critical only.

### Q33 🟡 Alert "silent hours"
Kelly wants to mute non-critical alerts 8 hours overnight; bilge still fires. Mechanism?
- **Recommended:** HA `input_boolean.quiet_hours` + schedule; bilge/fire/anchor-drag bypass the flag.

### Q34 🟢 Demo mode
Canned data for demos (yacht club, friends). Is this v1 or stretch?
- **Recommended:** **Stretch.** Prototype-only until someone actually asks to see the boat.

### Q35 🟢 Sign-off process
Who signs each phase's exit gate — Pete alone, or Pete + Kelly on Kelly-facing criteria (glance usability, alert-delivery)?
- **Recommended:** Pete alone for Phase 1–4; Pete + Kelly for Phase 5+ where Kelly-facing criteria land.

---

## G. Backup, DR, Governance

### Q36 🟡 Offsite backup destination
Rules forbid Backblaze B2 ($6/mo). Options: home NAS, friend's NAS, USB drive in drawer, or Pete's already-paid Google One.
- **Recommended:** Git-versioned HA config + weekly rsync to home NAS (if exists) + monthly USB-drive copy.

### Q37 🟡 Dedicated MQTT TLS sub-domain
Settle on `boat-broker.peteskrake.com`, `home-broker.peteskrake.com` vs. sub-domain pattern.
- **Recommended:** Use those two exact names. Simple and explicit.

### Q38 🟡 MQTT topic convention
`boat/hunter41/...` (boat name) vs `boat/<mmsi>/...` (generic).
- **Recommended:** **`boat/hunter41/...`** for v1. Single boat, readable topics. If Pete acquires a second boat, refactor then.

### Q39 🟢 Public repo?
Going public unlocks free Wokwi CI + GitHub Actions minutes; also enables community contributions.
- **Recommended:** **Yes, public.** Ties to Q25.

---

## H. Tier 6 — Existing-bus integration (Phase 11+, all post-v1)

Detail in [`nmea2000-integration.md`](nmea2000-integration.md). All resolved at survey or at Phase 11 start; none block v1.

| # | Question | Resolve when |
|---|---|---|
| Q40 | Does the Hunter 41DS have an N2K backbone? Chartplotter brand/era? | Survey |
| Q41 | What N2K connector type — Maretron Mini, NMEA Micro-C, DeviceNet? | Survey |
| Q42 | Engine bus — newer Yanmar with J1939, or older mechanical? | Engine plate |
| Q43 | Any 0183-only talkers (DSC VHF, autopilot, fluxgate, depth)? | Survey |
| Q44 | ✅ **RESOLVED** — Path A (DIY $60, CAN-ESP32 + ttlappalainen decoder) is the chosen integration approach for Phase 11a. Path B reserved if/when hand-rolled decoder list grows painful. | Resolved Apr 2026 |
| Q45 | Victron BMV/SmartShunt/MPPT installed with VE.Direct port? | Electrical inspection |
| Q46 | Cancel Phase 8 GPS hardware ($70) if N2K provides GPS? | Phase 11a exit |
| Q47 | Any safety-critical N2K data (engine alarm) for Tier 0 buzzer? | Phase 11a |
| Q48 | Tag Tier 6 MQTT data with `source=n2k` for distinguishing? | Topic-convention design |

---

## Summary — remaining questions (non-blocking)

All Top-10 blockers are resolved (§0 above). Remaining questions are implementation-time decisions that don't block Phase 1 kickoff:

- **Q3, Q4, Q5** — off-season behavior, AIS opt-in timing, remote-access UX (all post-Phase-6)
- **Q8, Q9, Q10, Q11** — actuator scope, connector philosophy, spares (v1.5+)
- **Q12, Q13, Q14, Q15, Q17** — install-time decisions (AIS antenna, tank senders, engine switch, CO alarm, marina WiFi)
- **Q19–Q23** — LVGL panel details (only relevant when Phase 10+ is live)
- **Q27, Q28, Q29** — time-acceleration in tests, HIL timing, LVGL harness
- **Q31–Q35** — alert-UX refinements that can be tuned after Phase 6 soak
- **Q36, Q37, Q38** — backup, TLS sub-domain names, MQTT topic convention (settle during Phase 2 setup)
