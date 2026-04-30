"""Step definitions for bilge-related scenarios.

The bilge float switch is a binary input on the boat. In virtual mode
the adapter publishes the canonical MQTT payload; in HIL mode it pulls
a GPIO; in live mode it routes through a test-mode injection topic.
The step text doesn't reflect any of that — see
planning/tdd-architecture.md §C for the layering.
"""
from __future__ import annotations

from pytest_bdd import given, when


@given("the bilge float switch reports water")
@when("the bilge float switch reports water")
async def bilge_reports_water(boat) -> None:
    await boat.set_bilge(True)


@given("the bilge float switch reports dry")
@when("the bilge float switch reports dry")
async def bilge_reports_dry(boat) -> None:
    await boat.set_bilge(False)
