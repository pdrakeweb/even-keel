"""MQTT publishing — telemetry, status, discovery, LWT, control listening.

Behavior:
- On startup, publishes Home Assistant discovery messages so HA auto-creates
  entities for every sensor in TOPIC_MAP.
- Listens for `boat/control/simulator/run` ("on"/"off") and
  `boat/control/simulator/scenario` (name).
- When run=on, generates a SensorSnapshot every PUBLISH_INTERVAL_S seconds
  and publishes to all canonical topics.
- When run=off, publishes status only (LWT, sim/active=0) and pauses telemetry.
- LWT publishes online=OFF if the simulator dies.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import time

import aiomqtt

from .discovery import build_discovery_payloads
from .scenarios import DEFAULT_SCENARIO, get_scenario, list_scenarios
from .sensors import (
    AIS_TARGETS_TOPIC,
    CTRL_RUN_TOPIC,
    CTRL_SCENARIO_TOPIC,
    LWT_TOPIC,
    LWT_PAYLOAD_OFFLINE,
    STATUS_ACTIVE_TOPIC,
    STATUS_SCENARIO_TOPIC,
    TOPIC_MAP,
    SensorSnapshot,
    serialize_ais_targets,
)

log = logging.getLogger("evenkeel_sim.publisher")

PUBLISH_INTERVAL_S = 1.0


class SimulatorPublisher:
    def __init__(
        self,
        broker: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        initial_scenario: str = DEFAULT_SCENARIO,
        run_initially: bool = True,
        rng: random.Random | None = None,
    ) -> None:
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.scenario_name = initial_scenario
        self.running = run_initially
        self.rng = rng or random.Random()
        self._scenario_start_time = time.monotonic()
        self._prev_snapshot = SensorSnapshot()

    async def run(self) -> None:
        log.info(
            "Connecting to MQTT %s:%s · initial scenario=%s · running=%s",
            self.broker, self.port, self.scenario_name, self.running,
        )
        will = aiomqtt.Will(
            topic=LWT_TOPIC,
            payload=LWT_PAYLOAD_OFFLINE,
            qos=1,
            retain=True,
        )
        async with aiomqtt.Client(
            hostname=self.broker,
            port=self.port,
            username=self.username,
            password=self.password,
            will=will,
            identifier=f"evenkeel-sim-{int(time.time())}",
        ) as client:
            log.info("MQTT connected. Publishing discovery + status …")
            await self._publish_discovery(client)
            await self._publish_status(client)
            await client.subscribe(CTRL_RUN_TOPIC)
            await client.subscribe(CTRL_SCENARIO_TOPIC)
            await asyncio.gather(
                self._control_loop(client),
                self._publish_loop(client),
            )

    async def _publish_discovery(self, client: aiomqtt.Client) -> None:
        for topic, payload in build_discovery_payloads():
            await client.publish(topic, json.dumps(payload), retain=True, qos=1)
        log.info("Published HA discovery for %d entities", len(TOPIC_MAP))

    async def _publish_status(self, client: aiomqtt.Client) -> None:
        await client.publish(STATUS_ACTIVE_TOPIC, "1" if self.running else "0",
                             retain=True, qos=1)
        await client.publish(STATUS_SCENARIO_TOPIC, self.scenario_name,
                             retain=True, qos=1)

    async def _control_loop(self, client: aiomqtt.Client) -> None:
        async for message in client.messages:
            payload = message.payload.decode("utf-8", errors="ignore").strip().lower()
            topic = str(message.topic)
            if topic == CTRL_RUN_TOPIC:
                new = payload in {"on", "1", "true", "yes"}
                if new != self.running:
                    log.info("Run flag changed: %s → %s", self.running, new)
                    self.running = new
                    await self._publish_status(client)
            elif topic == CTRL_SCENARIO_TOPIC:
                if payload not in list_scenarios():
                    log.warning("Ignoring unknown scenario: %r", payload)
                    continue
                if payload != self.scenario_name:
                    log.info("Scenario changed: %s → %s", self.scenario_name, payload)
                    self.scenario_name = payload
                    self._scenario_start_time = time.monotonic()
                    await self._publish_status(client)

    async def _publish_loop(self, client: aiomqtt.Client) -> None:
        while True:
            try:
                if self.running:
                    snap = self._next_snapshot()
                    await self._publish_snapshot(client, snap)
                    self._prev_snapshot = snap
                await asyncio.sleep(PUBLISH_INTERVAL_S)
            except Exception:  # noqa: BLE001
                log.exception("Publish loop error; continuing")
                await asyncio.sleep(2.0)

    def _next_snapshot(self) -> SensorSnapshot:
        elapsed = time.monotonic() - self._scenario_start_time
        scenario = get_scenario(self.scenario_name)
        return scenario(elapsed, self._prev_snapshot, self.rng)

    async def _publish_snapshot(self, client: aiomqtt.Client, snap: SensorSnapshot) -> None:
        d = snap.to_dict()
        for field, (topic, transform) in TOPIC_MAP.items():
            value = d[field]
            payload = transform(value)
            if payload is None:
                continue
            await client.publish(topic, payload, retain=True, qos=0)
        # AIS targets list as JSON
        await client.publish(AIS_TARGETS_TOPIC, serialize_ais_targets(snap.ais_targets),
                             retain=True, qos=0)
        # Boat device_tracker for HA map (state = "home"/"not_home"/zone, with lat/lon attrs)
        in_slip = snap.slip_distance_m < 30
        tracker_state = "home" if in_slip else "not_home"
        await client.publish("boat/hunter41/tracker/state", tracker_state, retain=True, qos=0)
        attrs = json.dumps({
            "latitude": snap.lat,
            "longitude": snap.lon,
            "gps_accuracy": 5,
            "heading": snap.heading_deg,
            "speed": snap.sog_kt,
            "source_type": "gps",
        })
        await client.publish("boat/hunter41/tracker/attrs", attrs, retain=True, qos=0)
