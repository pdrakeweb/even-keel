"""Step definitions for battery + shore-power scenarios.

The house battery's SoC and voltage are the single most-watched values
on the boat. Steps map directly to the BoatAdapter Protocol; the
underlying transport (simulator MQTT publish, HIL voltage divider,
live test-mode injection) is the adapter's problem.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, when


# ─── House battery ──────────────────────────────────────────────
@when(parsers.parse("the house battery reports {pct:g}% state of charge"))
async def house_reports_soc(boat, pct: float) -> None:
    await boat.set_house_soc(pct)


@when(parsers.parse("the house battery reports {volts:g} volts"))
async def house_reports_volts(boat, volts: float) -> None:
    await boat.set_house_voltage(volts)


# ─── Shore power ────────────────────────────────────────────────
@given("shore power is connected")
@when("shore power is connected")
async def shore_connected(boat) -> None:
    await boat.set_shore_power(True)


@given("shore power is disconnected")
@when("shore power is disconnected")
async def shore_disconnected(boat) -> None:
    await boat.set_shore_power(False)
