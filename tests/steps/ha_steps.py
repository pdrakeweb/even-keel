"""Step definitions for HA REST entity-state assertions.

Adds the "HA entity X equals Y within N seconds" predicate that
bridges the MQTT-side data plane (covered by common_steps) with the
HA-side template-sensor / discovery layer.

Tests using these steps require HA_URL + HA_TOKEN env vars. When
unset, the boat fixture's adapter has `has_ha=False` and these step
implementations call pytest.skip() with a clear reason — local dev
without HA stays green.
"""
from __future__ import annotations

import pytest
from pytest_bdd import parsers, then


@then(
    parsers.parse(
        'within {timeout:d} seconds HA entity "{entity_id}" equals "{expected}"'
    )
)
async def ha_entity_equals(boat, timeout: int, entity_id: str, expected: str) -> None:
    if not boat.has_ha:
        pytest.skip(
            "HA not configured (HA_URL + HA_TOKEN env vars unset); "
            "skipping HA-entity assertion"
        )
    actual = await boat.wait_for_entity_state(
        entity_id, expected, timeout=float(timeout)
    )
    assert actual == expected, f"{entity_id}: expected {expected!r}, got {actual!r}"
