"""Step definitions for AIS targets scenarios.

The simulator's `serialize_ais_targets()` is the contract — every
adapter (virtual, HIL, live) feeds it and emits byte-identical JSON.
Steps assemble AisTarget instances and ask the adapter to publish.
"""
from __future__ import annotations

import json

from evenkeel_sim.sensors import AisTarget
from pytest_bdd import given, parsers, then, when


@when(parsers.parse("zero AIS targets are reported"))
async def zero_ais_targets(boat) -> None:
    await boat.set_ais_targets([])


@when(parsers.parse('a Class B target named "{name}" at {range_nm:g} nm is reported'))
async def one_classb_target(boat, name: str, range_nm: float) -> None:
    target = AisTarget(
        mmsi=367123456,
        name=name,
        type="Class B",
        bearing_deg=45.0,
        range_nm=range_nm,
        cog_deg=180.0,
        sog_kt=4.5,
        age_s=2,
    )
    await boat.set_ais_targets([target])


@when(parsers.parse("{count:d} AIS targets are reported at ranges {ranges} nm"))
async def n_ais_targets(boat, count: int, ranges: str) -> None:
    range_values = [float(x) for x in ranges.split()]
    if len(range_values) != count:
        raise ValueError(
            f"step said {count} targets but supplied {len(range_values)} ranges"
        )
    targets = [
        AisTarget(
            mmsi=200_000_000 + i,
            name=f"TGT{i}",
            type="Class A",
            bearing_deg=10.0 * (i + 1),
            range_nm=r,
            cog_deg=90.0,
            sog_kt=8.0,
            age_s=3,
        )
        for i, r in enumerate(range_values)
    ]
    await boat.set_ais_targets(targets)


@then(parsers.parse(
    'within {timeout:d} seconds MQTT topic "{topic}" '
    "parses as a JSON array of {count:d} items"
))
async def topic_json_array_of_count(
    boat, timeout: int, topic: str, count: int
) -> None:
    def _matches(payload: bytes) -> bool:
        try:
            data = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
        return isinstance(data, list) and len(data) == count

    payload = await boat.wait_for(topic, predicate=_matches, timeout=float(timeout))
    data = json.loads(payload.decode("utf-8"))
    assert isinstance(data, list)
    assert len(data) == count, f"{topic}: expected {count} items, got {len(data)}"


@then(parsers.parse('the first AIS target on that topic has key "{key}"'))
async def first_target_has_key(boat, key: str) -> None:
    payload = await boat.mqtt_last("boat/hunter41/ais/targets")
    data = json.loads(payload.decode("utf-8"))
    assert isinstance(data, list) and data, "no AIS targets payload yet"
    assert key in data[0], f"first target missing key {key!r}; got {sorted(data[0])}"
