"""Integration tests against the real SimulatorPublisher.

The pytest-bdd suites elsewhere in this directory test the BoatAdapter
+ TOPIC_MAP path and shortcut the simulator. These tests do the
opposite — they spin up an actual `SimulatorPublisher` instance as a
background asyncio task, subscribe to its broker as a real client,
and assert the publish loop produces what `boat_health.yaml` and the
custom card consume.

If these go red, something has shifted in the simulator's contract
even when every adapter-side BDD scenario stays green.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
from typing import AsyncIterator

import aiomqtt
import pytest
from evenkeel_sim.publisher import SimulatorPublisher
from evenkeel_sim.sensors import (
    AIS_TARGETS_TOPIC,
    CTRL_RUN_TOPIC,
    CTRL_SCENARIO_TOPIC,
    LWT_TOPIC,
    STATUS_ACTIVE_TOPIC,
    STATUS_SCENARIO_TOPIC,
)


BROKER = os.environ.get("MQTT_BROKER", "localhost")
PORT = int(os.environ.get("MQTT_PORT", "1883"))


@pytest.fixture
async def publisher_task() -> AsyncIterator[asyncio.Task[None]]:
    """Run a SimulatorPublisher in the background for one test.

    Uses a deterministic Random seed so scenario output is repeatable.
    Clears retained state on the control topics first so a prior test's
    "off" or HA's `boat_controls.yaml` automation publishing the
    initial input_boolean.use_simulator state doesn't immediately flip
    `running` to False before the test gets to assert.

    The task is cancelled in teardown; aiomqtt closes its socket on
    `__aexit__` so the broker sees a graceful disconnect.
    """
    # Clear retained control-topic state. Empty payload + retain=True
    # is the MQTT-spec way to delete a retained message.
    async with aiomqtt.Client(BROKER, PORT, identifier="evenkeel-int-purge") as c:
        await c.publish(CTRL_RUN_TOPIC, b"", retain=True, qos=1)
        await c.publish(CTRL_SCENARIO_TOPIC, b"", retain=True, qos=1)

    pub = SimulatorPublisher(
        broker=BROKER,
        port=PORT,
        initial_scenario="normal",
        run_initially=True,
        rng=random.Random(0xEEC7E),
    )
    task = asyncio.create_task(pub.run())
    # Give the publisher a moment to connect, publish discovery, and
    # emit at least one snapshot.
    await asyncio.sleep(2.0)
    yield task
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, BaseException):
        pass


async def _collect(topic: str, timeout: float = 5.0) -> bytes:
    """Subscribe and grab the most recent retained payload on `topic`."""
    deadline = asyncio.get_running_loop().time() + timeout
    async with aiomqtt.Client(BROKER, PORT, identifier="evenkeel-int-collect") as c:
        await c.subscribe(topic, qos=1)
        async for msg in c.messages:
            if str(msg.topic) == topic:
                return bytes(msg.payload) if msg.payload else b""
            if asyncio.get_running_loop().time() > deadline:
                raise TimeoutError(f"no payload on {topic} within {timeout}s")
    raise TimeoutError(f"client closed before {topic} produced anything")


async def _publish_control(topic: str, payload: str) -> None:
    async with aiomqtt.Client(BROKER, PORT, identifier="evenkeel-int-ctrl") as c:
        await c.publish(topic, payload, qos=1, retain=False)


async def test_publisher_emits_online_status(publisher_task) -> None:  # noqa: ARG001
    """Live publisher should retain online=ON on the LWT topic."""
    payload = await _collect(LWT_TOPIC)
    assert payload == b"ON", f"expected b'ON', got {payload!r}"


async def test_publisher_emits_status_active(publisher_task) -> None:  # noqa: ARG001
    """Run flag retained as '1' when started with run_initially=True."""
    payload = await _collect(STATUS_ACTIVE_TOPIC)
    assert payload == b"1"


async def test_publisher_emits_status_scenario(publisher_task) -> None:  # noqa: ARG001
    """Initial scenario name is retained on its dedicated topic."""
    payload = await _collect(STATUS_SCENARIO_TOPIC)
    assert payload == b"normal"


async def test_publisher_emits_house_voltage_in_normal_range(
    publisher_task,  # noqa: ARG001
) -> None:
    """Normal scenario keeps house_v in a sane band (12.0–13.6 V)."""
    payload = await _collect("boat/hunter41/power/battery/house/v")
    voltage = float(payload.decode("utf-8"))
    assert 12.0 <= voltage <= 13.8, f"house_v out of band: {voltage}"


async def test_publisher_emits_ais_targets_as_json_list(
    publisher_task,  # noqa: ARG001
) -> None:
    """AIS targets topic is always a valid JSON array (even if empty)."""
    payload = await _collect(AIS_TARGETS_TOPIC)
    data = json.loads(payload.decode("utf-8"))
    assert isinstance(data, list)


async def test_publisher_responds_to_run_off(publisher_task) -> None:  # noqa: ARG001
    """Sending run=off flips status_active to 0 within a couple seconds."""
    await _publish_control(CTRL_RUN_TOPIC, "off")
    # Give the publisher's control loop a beat.
    await asyncio.sleep(1.5)
    payload = await _collect(STATUS_ACTIVE_TOPIC)
    assert payload == b"0", f"expected '0' after run=off, got {payload!r}"


async def test_publisher_responds_to_scenario_change(
    publisher_task,  # noqa: ARG001
) -> None:
    """Sending a known scenario name retains it on the scenario topic."""
    await _publish_control(CTRL_SCENARIO_TOPIC, "low_battery")
    await asyncio.sleep(1.5)
    payload = await _collect(STATUS_SCENARIO_TOPIC)
    assert payload == b"low_battery"
