"""Step definitions for leak-detection scenarios.

Three zone-keyed leak sensors (head, galley, engine bay). Each maps
to a separate boat/hunter41/leak/<zone> topic, mirroring the bilge
contract.
"""
from __future__ import annotations

from pytest_bdd import given, when


@given("the head reports a water leak")
@when("the head reports a water leak")
async def head_leak(boat) -> None:
    await boat.set_leak("head", True)


@when("the head leak clears")
async def head_leak_clears(boat) -> None:
    await boat.set_leak("head", False)


@when("the galley reports a water leak")
async def galley_leak(boat) -> None:
    await boat.set_leak("galley", True)


@when("the engine bay reports a water leak")
async def engine_bay_leak(boat) -> None:
    await boat.set_leak("engine_bay", True)
