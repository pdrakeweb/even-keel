# EvenKeel

A DIY sailboat monitoring, AIS, and alerting system for a Hunter 41DS on Lake Erie.

Built around a single ESP32-S3 on the boat, a Home Assistant instance at home, and a zero-subscription infrastructure — no cloud dependencies, no third-party integrations required, no ongoing costs.

## Status

**Planning complete.** Implementation not yet started. Phase 1 (bench AIS prototype) is the next step once the Top 10 open questions in [`planning/open-questions.md`](planning/open-questions.md) are resolved.

## Start here

1. [`planning/README.md`](planning/README.md) — map of the planning folder
2. [`planning/architecture.md`](planning/architecture.md) — one-diagram system view
3. [`planning/roadmap.md`](planning/roadmap.md) — phased implementation plan
4. [`planning/open-questions.md`](planning/open-questions.md) — what to answer next

## Repo layout

```
research/           original design docs (v1.0 and continuation brief)
planning/           research reports + synthesis
firmware/           ESPHome YAML (boat node + Tier 1 dashboard head)
tests/              pytest-bdd test harness (virtual / HIL / live modes)
hil-rig/            bench hardware-in-the-loop stimulator
home-assistant/     HA configuration (dashboards, themes, automations, packages)
simulator/          boat telemetry simulator — runtime-swappable with real hardware
relay/              optional aisstream.io forwarder
docs/               runbooks, photos, install guides — ui-dev-quickstart.md
tools/              one-off scripts (MQTT replay, AIS capture, cert rotation)
docker-compose.yml  local dev stack (mosquitto + HA + simulator)
```

## Develop the UI without hardware

```bash
cp home-assistant/secrets.yaml.example home-assistant/secrets.yaml
docker compose up -d
# open http://localhost:8123, toggle "Use simulated boat data"
```

See [`docs/ui-dev-quickstart.md`](docs/ui-dev-quickstart.md) for the full guide.

## Design principles

1. Reliability under marine conditions.
2. **No dependency on cloud subscriptions.** Every feature works with Pete's hardware only.
3. ESPHome YAML-first — minimal custom firmware.
4. Commercial, replaceable parts; no custom PCBs.
5. Phased: each phase ships working end-to-end functionality.
6. Test-driven: natural-language Gherkin scenarios run against a simulated boat AND against the real deployed system.
