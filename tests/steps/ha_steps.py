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
from pytest_bdd import given, parsers, then, when

# `within N seconds HA entity "X" equals "Y"` shows up in features as
# either a Then (the canonical assertion form), an And chained off a
# Given (mid-setup verification), or a When chained off a Then. Register
# under all three keywords — pytest-bdd 8 binds keywords strictly.
_HA_PARSER = parsers.parse(
    'within {timeout:d} seconds HA entity "{entity_id}" equals "{expected}"'
)


_HA_PRESENT_PARSER = parsers.parse(
    'within {timeout:d} seconds HA entity "{entity_id}" is present'
)
_HA_ABSENT_PARSER = parsers.parse(
    'within {timeout:d} seconds HA entity "{entity_id}" is absent'
)


@given(_HA_PRESENT_PARSER)
@when(_HA_PRESENT_PARSER)
@then(_HA_PRESENT_PARSER)
async def ha_entity_present(boat, timeout: int, entity_id: str) -> None:
    """Assert an HA entity exists (regardless of its state value).

    Useful for runtime-created entities — persistent_notification.*,
    helpers spawned by automations — where the state value varies by
    HA version but the entity's existence is the meaningful signal.
    """
    if not boat.has_ha:
        pytest.skip(
            "HA not configured (HA_URL + HA_TOKEN env vars unset); "
            "skipping HA-entity assertion"
        )
    await boat.wait_for_entity_present(entity_id, timeout=float(timeout))


@given(_HA_ABSENT_PARSER)
@when(_HA_ABSENT_PARSER)
@then(_HA_ABSENT_PARSER)
async def ha_entity_absent(boat, timeout: int, entity_id: str) -> None:
    """Assert an HA entity does NOT exist (returns 404 from /api/states).

    The dismissal counterpart to ha_entity_present. Used to verify
    persistent_notification.dismiss / runtime-created entity removal.
    """
    if not boat.has_ha:
        pytest.skip(
            "HA not configured (HA_URL + HA_TOKEN env vars unset); "
            "skipping HA-entity assertion"
        )
    await boat.wait_for_entity_absent(entity_id, timeout=float(timeout))


@given(_HA_PARSER)
@when(_HA_PARSER)
@then(_HA_PARSER)
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
