"""Step definitions for anchor-watch (Phase 9) scenarios.

Anchor armed/disarmed + drift distance map straight to the BoatAdapter
Protocol's `set_anchor()`. The "armed" half is a boolean topic; the
distance_m topic uses the same one-decimal contract as battery SoC.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, when


@when("the anchor is disarmed")
async def anchor_disarmed(boat) -> None:
    await boat.set_anchor(False, 0.0)


@given(parsers.parse("the anchor is armed at {distance_m:g} m drift"))
@when(parsers.parse("the anchor is armed at {distance_m:g} m drift"))
async def anchor_armed(boat, distance_m: float) -> None:
    await boat.set_anchor(True, distance_m)
