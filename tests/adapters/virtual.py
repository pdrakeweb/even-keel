"""Virtual-mode boat adapter.

In virtual mode the "boat" is the EvenKeel simulator, the broker is a
local Mosquitto, and Home Assistant is the same official Docker image
the production deployment uses. The adapter:

- Connects to the broker as a separate MQTT client (publisher AND
  subscriber — it acts as both stimulus and observer).
- Caches every retained payload it receives so step definitions can
  read "the last value on topic X" without race conditions.
- Drives the canonical TOPIC_MAP transforms when synthesizing
  payloads — the bytes on the wire are byte-for-byte the same as what
  `SimulatorPublisher` would publish.

Future iterations will spawn the simulator as a child process here
(or import its `SimulatorPublisher` directly into a background task)
so a feature can mix scenario-driven background telemetry with
explicit stimulus pokes. For now this adapter is the minimum viable
producer: it publishes exactly the values the test asks it to.
"""
from __future__ import annotations

import asyncio
import logging
import os
import pathlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

import aiomqtt


@dataclass
class _Waiter:
    """One pending wait_for() call.

    Pairs a future with the predicate that has to be satisfied before
    the listener resolves it. Replaces an earlier hack that stashed
    the predicate as a private attribute on the future.
    """
    future: "asyncio.Future[bytes]"
    predicate: Callable[[bytes], bool] | None
from evenkeel_sim.sensors import (
    AIS_TARGETS_TOPIC,
    LWT_TOPIC,
    TOPIC_MAP,
    AisTarget,
    serialize_ais_targets,
)

log = logging.getLogger("evenkeel_tests.virtual")


class VirtualAdapter:
    """BoatAdapter implementation against a local mosquitto broker."""

    def __init__(
        self,
        broker: str | None = None,
        port: int | None = None,
        client_id: str = "evenkeel-tests",
    ) -> None:
        self.broker = broker or os.environ.get("MQTT_BROKER", "localhost")
        self.port = port or int(os.environ.get("MQTT_PORT", "1883"))
        self.client_id = client_id

        self._client: aiomqtt.Client | None = None
        self._listener: asyncio.Task[None] | None = None
        self._latest: dict[str, bytes] = {}
        self._waiters: dict[str, list[_Waiter]] = defaultdict(list)
        self._connected = asyncio.Event()

    # ─── Lifecycle ───────────────────────────────────────────────
    async def startup(self) -> None:
        log.info("VirtualAdapter connecting to %s:%s", self.broker, self.port)
        self._client = aiomqtt.Client(
            hostname=self.broker,
            port=self.port,
            identifier=self.client_id,
        )
        await self._client.__aenter__()
        # Subscribe to everything under the boat tree so retained payloads
        # arrive immediately and live ones queue up for waiters.
        await self._client.subscribe("boat/#", qos=1)
        # Publish a fake-online retained message so steps that assume the
        # simulator is up have a baseline. Real virtual-mode deployments
        # would have the simulator process publishing this.
        await self._client.publish(LWT_TOPIC, "ON", retain=True, qos=1)
        self._listener = asyncio.create_task(self._listen())
        self._connected.set()
        # Give the broker a beat to deliver retained messages.
        await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        if self._listener:
            self._listener.cancel()
            try:
                await self._listener
            except (asyncio.CancelledError, BaseException):
                pass
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                log.exception("aiomqtt shutdown raised; ignoring")
        self._connected.clear()

    async def _listen(self) -> None:
        assert self._client is not None
        try:
            async for message in self._client.messages:
                topic = str(message.topic)
                payload = bytes(message.payload) if message.payload else b""
                self._latest[topic] = payload
                # Resolve any waiters whose predicate now matches.
                pending = self._waiters.get(topic, [])
                still_pending: list[_Waiter] = []
                for waiter in pending:
                    if waiter.future.done():
                        continue
                    if waiter.predicate is None or waiter.predicate(payload):
                        waiter.future.set_result(payload)
                    else:
                        still_pending.append(waiter)
                self._waiters[topic] = still_pending
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            log.exception("MQTT listener crashed")

    # ─── Internal publish helper ─────────────────────────────────
    async def _publish_field(self, field: str, value) -> None:
        """Publish `value` on the canonical topic for a SensorSnapshot field.

        Uses the same transform TOPIC_MAP defines so byte-for-byte output
        matches what the simulator publishes.
        """
        topic, transform = TOPIC_MAP[field]
        payload = transform(value)
        if payload is None:
            return
        assert self._client is not None
        await self._client.publish(topic, payload, retain=True, qos=1)
        # Update local cache eagerly so a same-task observation works
        # without round-tripping through the broker listener.
        self._latest[topic] = payload.encode("utf-8") if isinstance(payload, str) else payload

    # ─── Stimuli ────────────────────────────────────────────────
    async def set_bilge(self, wet: bool) -> None:
        await self._publish_field("bilge_wet", wet)

    async def set_shore_power(self, on: bool) -> None:
        await self._publish_field("shore_power", on)

    async def set_generator(self, on: bool) -> None:
        await self._publish_field("generator", on)

    async def set_house_voltage(self, volts: float) -> None:
        await self._publish_field("house_v", volts)

    async def set_starter_voltage(self, volts: float) -> None:
        await self._publish_field("start_v", volts)

    async def set_temperature(self, zone: str, celsius: float) -> None:
        # Map friendly zone name to SensorSnapshot field.
        zone_field = {
            "cabin": "cabin_temp_c",
            "v_berth": "v_berth_temp_c",
            "head": "head_temp_c",
            "galley": "galley_temp_c",
            "nav": "nav_temp_c",
            "engine": "engine_temp_c",
            "fridge": "fridge_temp_c",
            "freezer": "freezer_temp_c",
            "lazarette": "lazarette_temp_c",
        }.get(zone)
        if zone_field is None:
            raise ValueError(f"unknown temperature zone: {zone!r}")
        await self._publish_field(zone_field, celsius)

    async def set_engine_running(self, running: bool) -> None:
        await self._publish_field("engine_running", running)

    async def set_engine_rpm(self, rpm: int) -> None:
        await self._publish_field("engine_rpm", rpm)

    async def set_engine_coolant(self, celsius: float) -> None:
        await self._publish_field("engine_coolant_c", celsius)

    async def set_engine_oil_pressure(self, kpa: float) -> None:
        await self._publish_field("engine_oil_pressure_kpa", kpa)

    async def set_leak(self, zone: str, present: bool) -> None:
        zone_field = {
            "head": "leak_head",
            "galley": "leak_galley",
            "engine": "leak_engine",
            "engine_bay": "leak_engine",
        }.get(zone)
        if zone_field is None:
            raise ValueError(f"unknown leak zone: {zone!r}")
        await self._publish_field(zone_field, present)

    async def set_anchor(self, armed: bool, distance_m: float = 0.0) -> None:
        await self._publish_field("anchor_armed", armed)
        await self._publish_field("anchor_distance_m", distance_m)

    async def set_ais_targets(self, targets: list[AisTarget]) -> None:
        """Publish the canonical AIS-targets JSON list.

        Uses the simulator's `serialize_ais_targets()` so the JSON is
        byte-identical to what `SimulatorPublisher` would emit. Also
        updates the rollup count + nearest topic via TOPIC_MAP for
        consistency with what HA's MQTT integration consumes.
        """
        assert self._client is not None
        payload = serialize_ais_targets(targets)
        await self._client.publish(AIS_TARGETS_TOPIC, payload, retain=True, qos=1)
        self._latest[AIS_TARGETS_TOPIC] = payload.encode("utf-8")
        # Mirror the rollup fields the dashboard's iteration cards use.
        await self._publish_field("ais_targets_in_range", len(targets))
        if targets:
            nearest = min(targets, key=lambda t: t.range_nm)
            await self._publish_field("ais_nearest_name", nearest.name)
            await self._publish_field("ais_nearest_range_nm", nearest.range_nm)
        else:
            await self._publish_field("ais_nearest_name", "")
            await self._publish_field("ais_nearest_range_nm", 0.0)

    async def inject_victron(self, soc: float, current: float, ttg_min: int) -> None:
        await self._publish_field("house_soc", soc)
        await self._publish_field("house_a", current)
        await self._publish_field("house_ttg_min", ttg_min)

    async def replay_ais(self, path: pathlib.Path, rate: float = 1.0) -> None:  # noqa: ARG002
        # Implemented in a later iteration once pyais decoder + a stub
        # AIS-bridge endpoint live in the harness.
        raise NotImplementedError("AIS replay arrives in Phase 1/Iteration 3")

    async def set_gps_track(  # noqa: ARG002
        self, track: list[tuple[float, float, float]]
    ) -> None:
        raise NotImplementedError("GPS track replay arrives in Phase 8")

    # ─── Observations ───────────────────────────────────────────
    async def entity_state(self, entity_id: str) -> str:  # noqa: ARG002
        # HA REST integration arrives in Iteration 2E. For now, telemetry
        # tests assert directly on MQTT and skip HA entity assertions.
        raise NotImplementedError("HA REST observation arrives in Iteration 2E")

    async def wait_for_notification(  # noqa: ARG002
        self,
        predicate: Callable[[dict], bool],
        timeout: float,
    ) -> dict:
        raise NotImplementedError("HA notification observation arrives in Iteration 2E")

    async def mqtt_last(self, topic: str) -> bytes:
        await self._connected.wait()
        return self._latest.get(topic, b"")

    async def wait_for(
        self,
        topic: str,
        predicate: Callable[[bytes], bool] | None = None,
        timeout: float = 10.0,
    ) -> bytes:
        """Wait for a payload on `topic` matching `predicate` (default: any)."""
        await self._connected.wait()
        # Fast path: cached value already matches.
        cached = self._latest.get(topic)
        if cached is not None and (predicate is None or predicate(cached)):
            return cached
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[bytes] = loop.create_future()
        waiter = _Waiter(future=fut, predicate=predicate)
        self._waiters[topic].append(waiter)
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError as e:
            cached = self._latest.get(topic)
            raise TimeoutError(
                f"Timed out after {timeout}s waiting for {topic!r} "
                f"(last seen: {cached!r})"
            ) from e
