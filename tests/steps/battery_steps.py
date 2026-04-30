"""Step definitions for battery + shore-power scenarios.

The house battery's SoC and voltage are the single most-watched values
on the boat. Steps map directly to the BoatAdapter Protocol; the
underlying transport (simulator MQTT publish, HIL voltage divider,
live test-mode injection) is the adapter's problem.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, when


# ─── House battery ──────────────────────────────────────────────
# Registered under @given/@when so scenarios can chain "Given the
# house battery reports X% state of charge" (mid-setup) AND "When..."
# (state-change action). pytest-bdd 8 binds keyword strictly.
_SOC_PARSER = parsers.parse("the house battery reports {pct:g}% state of charge")
_VOLTS_PARSER = parsers.parse("the house battery reports {volts:g} volts")


@given(_SOC_PARSER)
@when(_SOC_PARSER)
async def house_reports_soc(boat, pct: float) -> None:
    await boat.set_house_soc(pct)


@given(_VOLTS_PARSER)
@when(_VOLTS_PARSER)
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
