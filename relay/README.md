# relay/

**Optional** Python service that forwards AIS AIVDM lines from the boat's TCP :6638 to aisstream.io.

**Off by default.** EvenKeel works fully without this. See [`../planning/infrastructure.md §4`](../planning/infrastructure.md) for the policy rationale.

## Where it runs

Recommended: as a Home Assistant add-on on the home HA Green. The AIS stream is already tunneled to home over WireGuard for local OpenCPN use; one more subscriber is free.

Alternative: as a systemd service on the boat Pi.

## Config

```yaml
source_tcp: boat-broker.peteskrake.com:6638
aisstream_api_key: !secret aisstream_api_key   # free contributor key; not a subscription
aisstream_url: wss://stream.aisstream.io/v0/stream
```

## Tests

The test harness (tests/) uses a mock aisstream endpoint in CI. Real contributor key lives only on home HA host, never in git.
