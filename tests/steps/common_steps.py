"""Step definitions shared across multiple feature files.

These steps deal with the boat's online status and generic MQTT
assertions. Capability-specific steps (bilge, battery, AIS) live in
sibling step modules and are imported by their test_*.py bindings.
"""
from __future__ import annotations

from pytest_bdd import given, parsers, then, when


@given("the boat is online")
async def boat_is_online(boat) -> None:
    payload = await boat.wait_for(
        "boat/hunter41/status/online",
        predicate=lambda b: b in (b"ON", b"1"),
        timeout=5.0,
    )
    assert payload, "boat/hunter41/status/online should be retained as ON"


# `within X seconds MQTT topic Y equals Z` shows up in feature files as
# either a `Then` (the canonical assertion form) or an `And` chained off
# a `Given` (mid-setup verification). pytest-bdd 7 binds each keyword
# strictly, so we register the step under all three.
_MQTT_PARSER = parsers.parse(
    'within {timeout:d} seconds MQTT topic "{topic}" equals "{expected}"'
)


@given(_MQTT_PARSER)
@when(_MQTT_PARSER)
@then(_MQTT_PARSER)
async def mqtt_topic_equals(boat, timeout: int, topic: str, expected: str) -> None:
    payload = await boat.wait_for(
        topic,
        predicate=lambda b: b.decode("utf-8", errors="replace") == expected,
        timeout=float(timeout),
    )
    actual = payload.decode("utf-8", errors="replace")
    assert actual == expected, f"{topic}: expected {expected!r}, got {actual!r}"
