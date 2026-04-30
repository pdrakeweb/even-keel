# home-assistant/

Home Assistant OS configuration for the home HA Green instance, versioned in git.

See [`../planning/architecture.md §2.4`](../planning/architecture.md) and [`../planning/infrastructure.md`](../planning/infrastructure.md) for the host/network design.

## Structure

```
home-assistant/
  configuration.yaml       # core HA config
  secrets.yaml.example     # template; real secrets.yaml is gitignored
  lovelace/
    kellys-card.yaml       # "How's My Boat" minimal glance view
    petes-dashboard.yaml   # full graphs + trends (Phase 10)
  automations/
    alerts_bilge.yaml
    alerts_battery.yaml
    alerts_offline.yaml
    alerts_shore_power.yaml
    alerts_anchor_drag.yaml    # Phase 9
  blueprints/
```

## Deploy

Pete's home HA Green runs a git-commit hook on every config change; the `main` branch is authoritative. Restore from git to a fresh HA Green in under 2 hours (see `planning/infrastructure.md §8`).
