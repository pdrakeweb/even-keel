"""Step definitions for engine telemetry scenarios.

Engine running, RPM, coolant temperature, and oil pressure each map
to a SensorSnapshot field; the adapter forwards via TOPIC_MAP. Steps
share the BoatAdapter contract — no awareness of the underlying
producer (simulator vs. ESP32 J1939 bridge).
"""
from __future__ import annotations

from pytest_bdd import parsers, when


@when("the engine is reported off")
async def engine_off(boat) -> None:
    await boat.set_engine_running(False)


@when("the engine is reported running")
async def engine_running(boat) -> None:
    await boat.set_engine_running(True)


@when(parsers.parse("the engine reports {rpm:d} RPM"))
async def engine_reports_rpm(boat, rpm: int) -> None:
    await boat.set_engine_rpm(rpm)


@when(parsers.parse("the engine coolant reports {celsius:g} C"))
async def engine_coolant(boat, celsius: float) -> None:
    await boat.set_engine_coolant(celsius)


@when(parsers.parse("the engine oil pressure reports {kpa:g} kPa"))
async def engine_oil_pressure(boat, kpa: float) -> None:
    await boat.set_engine_oil_pressure(kpa)
