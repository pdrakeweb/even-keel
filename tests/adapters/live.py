"""Live-integration boat adapter.

In live mode the "boat" is the real ESP32-S3 deployed on Pete's Hunter
41DS, the broker is the boat's production Mosquitto, and HA is the
production HA instance. The adapter pokes the boat through the
test-mode injection topic tree (see firmware/packages/test_mode.yaml)
rather than driving canonical topics directly. The boat firmware
gates on `test_mode_active` and synthesizes the canonical telemetry.

Used via:

    pytest --mode=live --broker=boat-broker.peteskrake.com

Currently a SKELETON. The HMAC-signed test/enable handshake described
in planning/tdd-architecture.md §C lands when Phase 6 ships. Until
then, attempting `--mode=live` raises a clear NotImplementedError so
nobody accidentally runs un-validated stimulus against a real boat.

Observation methods read from the canonical telemetry topics — same
contract as VirtualAdapter — so the same Gherkin step definitions
work in both modes.
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
from evenkeel_sim.sensors import AisTarget

log = logging.getLogger("evenkeel_tests.live")


@dataclass
class _Waiter:
    future: "asyncio.Future[bytes]"
    predicate: Callable[[bytes], bool] | None


class LiveIntegrationAdapter:
    """BoatAdapter implementation against deployed boat firmware.

    Stimuli go to boat/hunter41/test/<sensor>; the firmware
    synthesizes canonical telemetry behind the `test_mode_active`
    gate. Observations read from the canonical topics, identical to
    VirtualAdapter.
    """

    DEVICE_TOPIC = "boat/hunter41"
    TEST_TOPIC_PREFIX = "boat/hunter41/test"

    def __init__(
        self,
        broker: str | None = None,
        port: int | None = None,
        client_id: str = "evenkeel-live-tests",
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.broker = broker or os.environ.get("MQTT_BROKER", "localhost")
        self.port = port or int(os.environ.get("MQTT_PORT", "1883"))
        self.client_id = client_id
        self.username = username or os.environ.get("MQTT_USER")
        self.password = password or os.environ.get("MQTT_PASS")

        self._client: aiomqtt.Client | None = None
        self._listener: asyncio.Task[None] | None = None
        self._latest: dict[str, bytes] = {}
        self._waiters: dict[str, list[_Waiter]] = defaultdict(list)
        self._connected = asyncio.Event()
        self._test_mode_armed = False

    # ─── Lifecycle ───────────────────────────────────────────────
    async def startup(self) -> None:
        log.info(
            "LiveIntegrationAdapter connecting to %s:%s as %s",
            self.broker, self.port, self.client_id,
        )
        self._client = aiomqtt.Client(
            hostname=self.broker,
            port=self.port,
            identifier=self.client_id,
            username=self.username,
            password=self.password,
        )
        await self._client.__aenter__()
        await self._client.subscribe(f"{self.DEVICE_TOPIC}/#", qos=1)
        self._listener = asyncio.create_task(self._listen())
        self._connected.set()
        await asyncio.sleep(0.2)

        # Arm test mode on the deployed firmware. The HMAC handshake
        # protects against replay; until it lands, refuse to enter
        # live mode silently.
        await self._arm_test_mode()

    async def shutdown(self) -> None:
        if self._test_mode_armed:
            try:
                await self._client.publish(
                    f"{self.TEST_TOPIC_PREFIX}/enable",
                    "OFF",
                    qos=1,
                )
            except Exception:  # noqa: BLE001
                pass
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

    async def _arm_test_mode(self) -> None:
        # Phase 6: HMAC-signed nonce + ts payload. Until that lands
        # we deliberately refuse to enter live mode rather than
        # poking the real boat with un-authenticated stimuli.
        raise NotImplementedError(
            "LiveIntegrationAdapter requires the HMAC-signed test_mode "
            "handshake (planning/tdd-architecture.md §C). Lands with "
            "Phase 6 — for now, run --mode=virtual."
        )

    async def _listen(self) -> None:
        assert self._client is not None
        try:
            async for message in self._client.messages:
                topic = str(message.topic)
                payload = bytes(message.payload) if message.payload else b""
                self._latest[topic] = payload
                pending = self._waiters.get(topic, [])
                still_pending: list[_Waiter] = []
                for w in pending:
                    if w.future.done():
                        continue
                    if w.predicate is None or w.predicate(payload):
                        w.future.set_result(payload)
                    else:
                        still_pending.append(w)
                self._waiters[topic] = still_pending
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            log.exception("MQTT listener crashed")

    # ─── Stimulus helper ─────────────────────────────────────────
    async def _inject(self, sensor_path: str, payload: str) -> None:
        """Publish to boat/hunter41/test/<sensor_path>.

        The firmware's test_mode package (only present when boat-mon
        is built with the test_mode include) consumes these and
        synthesizes the canonical telemetry topic.
        """
        if not self._test_mode_armed:
            raise RuntimeError("test mode not armed — call startup() first")
        assert self._client is not None
        topic = f"{self.TEST_TOPIC_PREFIX}/{sensor_path}"
        await self._client.publish(topic, payload, qos=1, retain=False)

    # ─── Stimuli (mirror BoatAdapter Protocol) ──────────────────
    async def set_bilge(self, wet: bool) -> None:
        await self._inject("bilge", "1" if wet else "0")

    async def set_shore_power(self, on: bool) -> None:
        await self._inject("shore", "1" if on else "0")

    async def set_generator(self, on: bool) -> None:
        await self._inject("generator", "1" if on else "0")

    async def set_house_voltage(self, volts: float) -> None:
        await self._inject("house_v", f"{volts:.2f}")

    async def set_house_soc(self, percent: float) -> None:
        await self._inject("house_soc", f"{percent:.1f}")

    async def set_starter_voltage(self, volts: float) -> None:
        await self._inject("start_v", f"{volts:.2f}")

    async def set_temperature(self, zone: str, celsius: float) -> None:
        await self._inject(f"temp/{zone}", f"{celsius:.1f}")

    async def set_engine_running(self, running: bool) -> None:
        await self._inject("engine/running", "1" if running else "0")

    async def set_engine_rpm(self, rpm: int) -> None:
        await self._inject("engine/rpm", str(int(rpm)))

    async def set_engine_coolant(self, celsius: float) -> None:
        await self._inject("engine/coolant", f"{celsius:.1f}")

    async def set_engine_oil_pressure(self, kpa: float) -> None:
        await self._inject("engine/oil_pressure", f"{kpa:.1f}")

    async def set_leak(self, zone: str, present: bool) -> None:
        await self._inject(f"leak/{zone}", "1" if present else "0")

    async def set_anchor(self, armed: bool, distance_m: float = 0.0) -> None:
        await self._inject("anchor/armed", "1" if armed else "0")
        await self._inject("anchor/distance_m", f"{distance_m:.1f}")

    async def set_ais_targets(self, targets: list[AisTarget]) -> None:  # noqa: ARG002
        # AIS injection routes through the simulated dAISy UART feed,
        # not test/* topics. Lands with Phase 1 in the live mode.
        raise NotImplementedError("Live AIS injection lands with Phase 1")

    async def inject_victron(self, soc: float, current: float, ttg_min: int) -> None:
        await self._inject("victron/soc", f"{soc:.1f}")
        await self._inject("victron/a", f"{current:.2f}")
        await self._inject("victron/ttg_min", str(int(ttg_min)))

    async def replay_ais(self, path: pathlib.Path, rate: float = 1.0) -> None:  # noqa: ARG002
        raise NotImplementedError("Live AIS replay lands with Phase 1")

    async def set_gps_track(  # noqa: ARG002
        self, track: list[tuple[float, float, float]]
    ) -> None:
        raise NotImplementedError("Live GPS track replay lands with Phase 8")

    # ─── Observations (canonical topics) ────────────────────────
    async def entity_state(self, entity_id: str) -> str:  # noqa: ARG002
        raise NotImplementedError(
            "HA REST observation lands with the next iteration "
            "(adds httpx + a configured HA token to the live setup)."
        )

    async def wait_for_notification(  # noqa: ARG002
        self,
        predicate: Callable[[dict], bool],
        timeout: float,
    ) -> dict:
        raise NotImplementedError("HA WebSocket notification lands with HA REST")

    async def mqtt_last(self, topic: str) -> bytes:
        await self._connected.wait()
        return self._latest.get(topic, b"")

    async def wait_for(
        self,
        topic: str,
        predicate: Callable[[bytes], bool] | None = None,
        timeout: float = 10.0,
    ) -> bytes:
        await self._connected.wait()
        cached = self._latest.get(topic)
        if cached is not None and (predicate is None or predicate(cached)):
            return cached
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[bytes] = loop.create_future()
        self._waiters[topic].append(_Waiter(future=fut, predicate=predicate))
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError as e:
            cached = self._latest.get(topic)
            raise TimeoutError(
                f"Timed out after {timeout}s waiting for {topic!r} "
                f"(last seen: {cached!r})"
            ) from e
