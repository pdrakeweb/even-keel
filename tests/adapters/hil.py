"""Hardware-in-the-loop boat adapter.

In HIL mode the "boat" is a bench rig (hil-rig/) that physically
stimulates the deployed firmware via real GPIOs, I²C, UART, and
opto-isolators rather than via MQTT topics. The rig is driven over a
USB serial link from the test runner; this adapter speaks that
protocol.

Currently a SKELETON. Phase 4-ish iteration on the HIL hardware lands
the actual stimulus protocol — until then `--mode=hil` raises a clear
NotImplementedError so nobody mistakes it for a working path.

Observation methods MAY use MQTT (the rig's ESP32 publishes its
sensed-state echo through Mosquitto) OR a direct serial query. The
choice is made by the rig protocol; either way step definitions don't
need to know.
"""
from __future__ import annotations

import logging
import pathlib
from typing import Callable

from evenkeel_sim.sensors import AisTarget

log = logging.getLogger("evenkeel_tests.hil")


class HilAdapter:
    """BoatAdapter implementation against a bench HIL rig.

    The rig is a separate ESP32-S3 running stimulator firmware that
    physically drives GPIOs / I²C / UART on the device-under-test.
    Communication is via USB serial — typically /dev/ttyUSB0 on Linux
    or COM3 on Windows; passed in via --hil-port.
    """

    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 115200) -> None:
        self.port = port
        self.baud = baud
        # Future: self._serial = serial.Serial(port, baud, timeout=1)
        # Future: self._mqtt = aiomqtt.Client(...) for observation echo

    # ─── Lifecycle ───────────────────────────────────────────────
    async def startup(self) -> None:
        raise NotImplementedError(
            "HIL mode requires the bench-rig stimulator firmware "
            "(hil-rig/) and its serial protocol. Lands with Phase 4 "
            "commissioning — for now, run --mode=virtual."
        )

    async def shutdown(self) -> None:
        # Idempotent — also the path executed if startup raised before
        # any resources were acquired.
        pass

    # ─── Stimuli ────────────────────────────────────────────────
    async def set_bilge(self, wet: bool) -> None: ...
    async def set_shore_power(self, on: bool) -> None: ...
    async def set_generator(self, on: bool) -> None: ...
    async def set_house_voltage(self, volts: float) -> None: ...
    async def set_house_soc(self, percent: float) -> None: ...
    async def set_starter_voltage(self, volts: float) -> None: ...
    async def set_temperature(self, zone: str, celsius: float) -> None: ...
    async def set_engine_running(self, running: bool) -> None: ...
    async def set_engine_rpm(self, rpm: int) -> None: ...
    async def set_engine_coolant(self, celsius: float) -> None: ...
    async def set_engine_oil_pressure(self, kpa: float) -> None: ...
    async def set_leak(self, zone: str, present: bool) -> None: ...
    async def set_anchor(self, armed: bool, distance_m: float = 0.0) -> None: ...
    async def set_ais_targets(self, targets: list[AisTarget]) -> None: ...
    async def inject_victron(self, soc: float, current: float, ttg_min: int) -> None: ...
    async def replay_ais(self, path: pathlib.Path, rate: float = 1.0) -> None: ...
    async def set_gps_track(
        self, track: list[tuple[float, float, float]]
    ) -> None: ...

    # ─── Observations ───────────────────────────────────────────
    async def entity_state(self, entity_id: str) -> str: ...

    async def wait_for_notification(
        self,
        predicate: Callable[[dict], bool],
        timeout: float,
    ) -> dict: ...

    async def mqtt_last(self, topic: str) -> bytes:
        return b""

    async def wait_for(
        self,
        topic: str,
        predicate: Callable[[bytes], bool] | None = None,
        timeout: float = 10.0,
    ) -> bytes:
        raise NotImplementedError("HIL observation lands with the rig protocol")
