# EvenKeel — Zero-Subscription Infrastructure Architecture

**Project:** EvenKeel — DIY sailboat monitoring for the Hunter 41DS.
**Supersedes:** Cloud-dependent sections of `sailboat-monitor-design.md` v1.0 (Oracle Cloud Mosquitto + Python AIS relay).
**Design principle:** Fully operational with *zero* cloud dependencies. Any cloud-touching feature must be optional and trivially removable.
**Document version:** 2.0 — April 2026.

---

## 1. Governing Rules

1. **No subscription fees**, ever. Not $0-today-maybe-later ("free tier" clouds), not $6.50/mo, not $1/mo.
2. **No mandatory third-party integration.** The boat and the house keep working if every external company vanishes.
3. **Hardware is a one-time cost.** A $99 Home Assistant Green is acceptable. A $6/mo backup service is not.
4. **Optional cloud features are welcome** if they can be toggled off in one config file and degrade only *nice-to-haves*.
5. **Pete's existing domain** (already owned, annually renewed) is treated as a fixed asset, not a subscription.
6. **The home network is not in the critical path.** EvenKeel's core functions — local dashboards, Tier 0 alarm, direct-to-phone Pushover — must work when home router/ISP/HA are any combination of unreachable. Home HA is the *default* and *preferred* alert-delivery path, not a dependency.

Under these rules, Oracle Cloud Always Free is **out** (policy risk + third-party). aisstream.io is **out as a required path**, **in as an opt-in contribution** (see §4).

---

## 2. Recommended Architecture — "On-Boat Broker + Home HA over WireGuard"

The broker lives on the boat. Home Assistant lives at home. They meet over WireGuard. Everything critical works when the internet between them fails.

### 2.1 ASCII topology (recommended default)

```
┌───────────────────────── HUNTER 41DS ──────────────────────────┐
│                                                                │
│  ESP32-S3 "BoatMon-1"  ──MQTT/TLS──▶  Mosquitto (local)        │
│    • AIS TCP :6638  ──────────────▶   on Pi 4 (HA OS + add-on) │
│    • sensor telemetry               ▲                          │
│                                     │ (localhost / boat LAN)   │
│                                     │                          │
│  Onboard LTE router (X75, 4×4 MIMO, WireGuard CLIENT)          │
│    • connects outbound to home WG endpoint                     │
│    • boat LAN 10.20.0.0/24                                     │
└────────────────────────────┬───────────────────────────────────┘
                             │ WireGuard tunnel
                             │ (home router = server, CGNAT-safe)
                             ▼
┌───────────────────────── HOME ─────────────────────────────────┐
│                                                                │
│  Home router (WG SERVER) ── LAN ── HA Green (Home Assistant OS)│
│                                    • WG peer of boat + mobile  │
│                                    • Mosquitto add-on (bridge) │
│                                    • Recorder / automations    │
│                                    • (opt) AIS-forwarder add-on│
│                                                                │
│  Kelly's 10" tablet (Fully Kiosk PWA) ── home LAN ── HA        │
│                                                                │
└────────────────────────────────────────────────────────────────┘

Optional branches (any can be removed without loss of core function):
  ─── Cloudflare Tunnel ──▶ home HA   (for Pete's phone remote access)
  ─── AIS forwarder ────────▶ aisstream.io  (opt-in contribution)
```

### 2.2 Why the broker moves to the boat

In the prior design, the boat ESP32 published *up* to a cloud broker. Inverted here: the broker **is on the boat**, and home HA is a subscriber.

Consequences:
- **Zero-cloud critical path.** Bilge alarms reach Kelly's tablet through home LAN ← home HA ← WireGuard ← boat broker. No internet-hop required for data to *exist*; only to *cross from boat to home*.
- **At the slip with router on:** everything normal.
- **Boat router off (boat "asleep"):** boat broker goes away along with the ESP32 itself. HA shows boat offline via retained LWT + heartbeat timeout. No degradation vs. prior design.
- **Home internet down, boat router up:** boat keeps collecting and retaining. Bridge reconnects when home is back. Retained topics recovered; high-frequency history lost (same as prior design).
- **Home internet and boat LTE both up, but boat LTE is CGNAT'd:** home is the WG server, boat is the client — outbound-only, CGNAT-safe.

### 2.3 CGNAT on LTE — practical mitigation

Most consumer LTE SIMs are CGNAT'd. **Home is the WireGuard server**, boat router the client. Both the boat and Pete's phone dial in. Home ISP needs a port-forward on UDP :51820 to the home router. Pete has confirmed the home router can expose this port.

### 2.3.1 WireGuard security posture on the exposed port

Exposing UDP :51820 publicly is standard WG practice and low-risk:

- **WireGuard is silent to non-peers.** A packet without a valid peer signature gets no response — there's nothing to enumerate, no banner, no handshake. Port scanners see a closed port.
- **Hardening in depth:**
  - No other inbound ports are forwarded.
  - Home router firewall drops all non-WG traffic at UDP :51820 (default for most firmware).
  - Peer keypairs are regenerated at least annually (calendar reminder in HA).
  - `PersistentKeepalive` is only on the peer configs, not the server (server responds only to known peers).
  - If the home router supports it, rate-limit inbound UDP :51820 to ~100 pkt/s (protects against UDP amplification, not against legitimate flaps).
- **What to do if compromised:** revoke all peer keys via `wg set <iface> peer <key> remove`; regenerate server keypair; re-distribute public key to boat router + Pete's phone. ~15 min operation.

If home becomes CGNAT'd in the future, switch to Cloudflare Tunnel as the non-WG optional convenience layer; EvenKeel core function is unaffected either way.

### 2.4 Bandwidth budget on LTE

Assume MQTT QoS 0, most topics every 60 s. With ~25 topics + AIS TCP bridge to home:

| Path | Typical | Peak |
|---|---|---|
| MQTT telemetry (bridge fan-out over WG) | ~2 KB/min | ~10 KB/min |
| WireGuard overhead | +20% | +20% |
| AIS contribution (~30 vessels visible) | ~8 KB/min | ~20 KB/min |
| HA ↔ broker keepalives | <1 KB/min | <1 KB/min |
| **Total per day (telemetry only)** | **~5 MB** | **~20 MB** |
| **Total per day (telemetry + AIS forwarding)** | **~17 MB** | **~50 MB** |

Even a 1 GB/mo LTE plan is unstressed.

### 2.5 WireGuard stability on cellular

- `PersistentKeepalive = 25` on the boat-side peer.
- MTU 1380 (safe under most carrier encapsulation).
- Router firmware with auto-reconnect on tunnel failure.

Field-stable. The well-known failure mode is the LTE router *itself* rebooting (kills tunnel and broker simultaneously) — router problem, not WG problem.

---

## 3. Bridged Broker Architecture (the stretch goal, now the default)

What was a "stretch goal" in v1 is the primary design here. Two brokers:

- **Boat broker** (Mosquitto on the on-boat HA Pi) — ESP32's only MQTT target.
- **Home broker** (Mosquitto add-on on home HA) — bridges to boat broker, HA's only MQTT target.

Why two brokers instead of HA-subscribes-directly-to-boat-broker:
- HA's MQTT integration behaves better against a *local* broker. Reconnect logic, retained message handling, auto-discovery all work predictably.
- The bridge is the single place responsible for WireGuard flakiness. HA never sees the tunnel; it sees only "MQTT up/down on localhost."
- Retained messages survive home internet outages — the home broker keeps serving HA the last known values while the bridge reconnects in background.

### Bridge config sketch (`mosquitto.conf` on home broker)

```
connection boat-bridge
address 10.20.0.1:8883
bridge_cafile /ssl/ca.crt
remote_username home-bridge
remote_password <secret>
topic boat/# both 1
cleansession false
notifications true
try_private false
```

State-during-partition behavior:
- **Boat ↔ home partition:** home HA shows last retained values (stale but present). Automations keyed on "fresh data" fire via HA heartbeat timeout.
- **Partition heals:** bridge reconnects, retained topics replay, HA resumes live updates. High-frequency history during gap is lost — accepted.

---

## 4. AIS Contribution to aisstream.io — Is It Allowed?

### Rule as written
> "No special cloud deployments or third-party integrations with subscription cost."

aisstream.io is (a) free to contribute to, (b) free to consume from (with rate limits), (c) has no login tied to credit card. It is a **third-party integration** but has **no subscription cost**.

### Ruling
**Allowed, if and only if it is optional.** The boat must function fully without it. The AIS forwarder is an *opt-in* add-on. aisstream.io going away tomorrow costs Pete nothing except the karma of contributing.

### Where the forwarder runs

| Location | Pros | Cons |
|---|---|---|
| **On the boat Pi** | Simple; runs only when boat is online | Consumes LTE data (~8 KB/min) |
| **On the home HA host** | Free bandwidth; keeps running when boat is online regardless of home user | Won't forward when boat↔home tunnel is down |
| **Nowhere (default)** | Zero cloud touch | No contribution |

**Recommendation:** run it at home as an HA add-on. The AIS stream is already tunneled to home for local OpenCPN use; one more subscriber is free.

---

## 5. Remote Access to HA (Pete on phone at work)

Ranked by fit to the rules:

### Option A — Nabu Casa HA Cloud ($6.50/mo)
**Forbidden.** Subscription.

### Option B — Home HA + public DNS + Let's Encrypt + NGINX + port forward
- **Cost:** $0 (domain already owned).
- **Rule compliance:** clean.
- **Requires:** home ISP not CGNAT; port 443 forwarded.
- **Risk:** exposes HA login publicly. Mitigate with fail2ban + IP allow list + HA MFA.

### Option C — Tailscale Free (personal tier)
- **Cost today:** $0, very generous (100 devices, 3 users).
- **Is it a subscription?** Free personal plan has no payment on file, no expiration. Operationally same as Let's Encrypt.
- **Risk:** third-party. If Tailscale changes free tier, Pete loses remote access (but not boat function).
- **Ruling:** allowed as optional, not as the only path.

### Option D — WireGuard to home router
- **Cost:** $0. Uses the same WG infrastructure already required for boat ↔ home.
- **Compliance:** perfect.
- **UX:** Pete must enable the WG profile on his phone before browsing.

### Option E — Cloudflare Tunnel (cloudflared, free)
- **Cost:** $0. No payment on file. No expiration.
- **Compliance:** third-party in data path, but free.
- **UX:** excellent. `https://ha.peteskrake.com` works from anywhere, no VPN, no port forward, CGNAT-safe.
- **Risk:** Cloudflare terms can change; free tunnel could end. Optional and replaceable with Option D in ~1 hour.

### Recommendation

**Primary: Option D (WireGuard to home).** Zero third parties; same tunnel we're already running.
**Optional convenience layer: Option E (Cloudflare Tunnel).** Install if; if it ever goes away, Option D is the fallback.

Skip Options A, B, C.

---

## 6. Hardware Comparison

### 6.1 Home HA hosting

| Host | Cost | Power | HA OS support | Maintenance | 10-yr horizon |
|---|---|---|---|---|---|
| **Home Assistant Green** | $99 | ~3 W | First-class | Lowest (OS auto-updates) | Very good — official product |
| **Raspberry Pi 5 8GB + NVMe + SSD + case** | ~$160 | ~4–6 W | First-class | Low | Excellent |
| **Intel N100 mini PC** | ~$150 | ~6–10 W | HAOS via Proxmox or bare metal | Medium (BIOS/firmware) | Excellent |
| **Old laptop + HAOS VM** | $0 | 15–30 W | HAOS as VM | Medium-High | Limited |

**Recommendation: HA Green at home.** $99 one-time, purpose-built by HA team. Pi 5 is a fine Plan B if Pete wants SSD speed for recorder.

### 6.2 On-boat HA + broker hosting

| Host | Cost | Idle W | Typical W | HA OS | Notes |
|---|---|---|---|---|---|
| **Pi Zero 2 W** | $15 | ~0.5 | ~0.8 | No (too little RAM) | Cheapest; broker-only role |
| **Pi 4 2GB + SSD** | ~$60 | ~2.5 | ~3.5 | Marginal | Sweet spot for broker + small HA |
| **Pi 4 4GB + SSD** | ~$75 | ~2.5 | ~3.5 | Yes | Preferred for HAOS + add-ons |
| **Pi 5 4GB + SSD** | ~$90 | ~3.0 | ~5–7 | Yes | Over-powered for boat |
| **Libre Le Potato + Debian + Docker** | ~$35 | ~1.5 | ~2.5 | Community only | More admin work |
| **Beelink N100** | ~$150 | ~6 | ~10 | Yes | Overkill |

**Recommendation: Raspberry Pi 4 4GB + 128 GB SSD over USB 3.0**, running HA OS. Runs Mosquitto add-on, local HA, ESPHome dashboard. ~3.5 W typical = ~0.3 Ah/hr at 12 V. 300 Ah house bank handles forever.

---

## 7. Certificates and DNS Without Subscriptions

### 7.1 Pete's domain
Already owned. Annual renewal — not a subscription in the forbidden sense. If it lapses, LAN and WireGuard pieces still function; remote-access names via Cloudflare Tunnel and public HA DNS stop resolving.

### 7.2 Let's Encrypt via DNS-01
Keep the existing design. DNS-01 works whether or not the boat is internet-reachable during renewal.

### 7.3 TLS on the internal MQTT broker — is it needed inside WireGuard?

**Yes — TLS on.** Defense in depth; consistent config; no cost. Use DNS-01 against a boat-side FQDN (e.g., `boat-mqtt.peteskrake.com`) resolving to a WG IP. Renew from **home HA** (stable internet) and ship the cert to the boat via Ansible or an `mqtt-cert-bundle` MQTT topic.

---

## 8. Backup and DR

### 8.1 HA config versioning
- **Git repo** of `/config` on home HA. Automated commit hook on every config change. No subscription.
- **On-boat HA config** similarly versioned; auto-pushed over WG when internet is up.

### 8.2 Offsite backup
Rules preclude Backblaze B2 ($6/mo).

1. **Home NAS / second drive at home** — truly $0 ongoing.
2. **NAS at a friend's house or Pete's office** over WG — free.
3. **rsync.net metered** — subscription. **Forbidden.**
4. **Pete's existing already-paid cloud** (e.g., existing Google One). If not *new* spend, acceptable.

**Recommendation: Git repo + weekly `rsync` to home NAS + monthly USB-drive copy.** Zero new spend.

---

## 9. Failure-Mode Analysis

| Failure | What degrades | What keeps working | Recovery |
|---|---|---|---|
| **LTE router dies** | Remote visibility; AIS contribution; OTA | Boat broker + ESP32 on boat LAN; bilge alarm buzzer; chartplotter AIS TCP | Reboot router at next visit |
| **Home internet dies** | Remote access from Pete's phone; home AIS forwarder | Boat full telemetry on boat broker; home HA shows last-known values; Kelly's tablet on home LAN keeps working | Bridge auto-reconnects |
| **Boat broker dies** (Pi crash, SD fail) | All MQTT on boat; AIS TCP to home; HA marks boat offline | AIS TCP server on ESP32 itself still serves chartplotter; home HA shows last-known | Pete reboots Pi at next visit |
| **Home HA dies** | Dashboards; automations; alerts; recorder | Boat broker keeps accepting publishes; ESP32 keeps publishing; bilge buzzer continues | Restore from Git-backed config to spare Pi in <1 hr |
| **Domain expires** | Cloudflare Tunnel name; public HA URL; DNS-01 next renewal | Everything on LAN/WG (IPs/internal hostnames) | Renew domain |
| **WireGuard tunnel down** | Home↔boat bridge; home AIS forwarder; OTA | Boat broker local; ESP32 local; home HA last-known | Auto re-establishes |
| **aisstream.io API change** | AIS contribution | All core function — AIS is opt-in | Update/disable forwarder |
| **Cloudflare free tier ends** | Easy phone access | WireGuard remote access still works | Remove tunnel config |
| **HA Green dies** | Home HA for days until replaced | Boat broker + ESP32 keep collecting; Kelly loses dashboard | Restore backup to spare Pi 5 |

---

## 10. Ruling on Specific Third Parties

| Service | Verdict | Reasoning |
|---|---|---|
| **Oracle Cloud Always Free** | **NOT ALLOWED** as runtime dependency | Corporate free tier; policy-change risk |
| **aisstream.io** | **ALLOWED as optional contribution** | Zero cost; not in critical path |
| **Tailscale Free** | **ALLOWED as optional remote access** | No subscription; not in critical path |
| **Cloudflare Tunnel (free)** | **ALLOWED as optional convenience** | Same posture as Tailscale Free |
| **Let's Encrypt** | **ALLOWED (core)** | Non-commercial foundation; free |
| **Pushover** | **ALLOWED (critical path)** | One-time $5 app fee per platform; no subscription. Used for home-independent critical alerts direct from boat ESP32. |
| **Twilio SMS** | **ALLOWED as opt-in plugin** | Only if user brings their own Twilio subscription. Not a project requirement. Example integration provided in `home-assistant/blueprints/`. |
| **Nabu Casa** | **NOT ALLOWED** | Subscription |
| **Backblaze B2 / rsync.net metered** | **NOT ALLOWED** | Subscription |
| **Pete's registrar** | **ALLOWED** | Domain ownership is infrastructure |

---

## 11. Recommendation

Adopt the **bridged-broker architecture** (§3):

- **Boat:** Raspberry Pi 4 4GB + USB SSD running HA OS. Mosquitto add-on = primary MQTT broker. ESP32 publishes here. AIS TCP :6638 exposed on boat LAN.
- **Home:** Home Assistant Green running full HA + Mosquitto add-on (bridge client) + ESPHome dashboard + optional AIS-forwarder add-on.
- **Network:** Home router is the WireGuard server. Boat router is a client. Pete's phone is a client. One tunnel for everything.
- **Remote phone access:** WireGuard to home is primary. Cloudflare Tunnel optional convenience.
- **AIS to aisstream.io:** off by default; HA add-on toggle to enable.
- **TLS:** Let's Encrypt DNS-01 via Pete's domain for everything, renewed from home HA.
- **Backup:** Git-versioned HA config + weekly local NAS rsync + monthly USB-drive copy.
- **DR target:** Complete rebuild from clean HA Green + Git repo in under 2 hours.

This preserves every capability of the prior OCI design while moving the critical path entirely onto Pete's hardware.

---

## 12. Open Questions for Pete

1. Does the onboard X75 router support WireGuard as a **client** with `PersistentKeepalive`?
2. Does Pete's home ISP currently CGNAT, or is port-forward for WG UDP :51820 available?
3. Does Pete's LTE carrier hand out routable IPv6 on the boat SIM? (Fallback design.)
4. Will Kelly's tablet stay on home LAN, or should it work at in-laws' house too?
5. Home NAS already, or "drawer with USB drive"?
6. "Boat asleep, no telemetry" acceptable off-season, or low-power always-on boat-side broker?
7. AIS contribution: opt-in from day one, or postponed until v1 is stable?
8. Remote phone access: WireGuard-only, or add Cloudflare Tunnel from start?
9. On-boat HA local dashboard or headless broker only? (Ties to local-dashboard.md.)
10. Boat Pi also runs ESPHome dashboard (for on-site OTA without WG), or only at home?

---

*End of document v2.0.*
