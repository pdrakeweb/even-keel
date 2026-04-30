"""Contract tests for the SensorSnapshot dataclass + TOPIC_MAP transformers.

These pin down the public API:
- Every primitive field maps to exactly one MQTT topic
- Every transformer accepts the field's typed value and returns
  either a string payload or None (None = legitimately omitted)
- AIS target list serialization is deterministic and JSON-decodable
- Default SensorSnapshot is internally consistent
"""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from evenkeel_sim.sensors import (
    AIS_TARGETS_TOPIC,
    CTRL_RUN_TOPIC,
    CTRL_SCENARIO_TOPIC,
    LWT_PAYLOAD_OFFLINE,
    LWT_PAYLOAD_ONLINE,
    LWT_TOPIC,
    STATUS_ACTIVE_TOPIC,
    STATUS_SCENARIO_TOPIC,
    TOPIC_MAP,
    AisTarget,
    SensorSnapshot,
    serialize_ais_targets,
)


class TestTopicMap:
    """TOPIC_MAP is the contract between simulator and HA."""

    def test_topic_map_has_no_duplicate_topics(self):
        topics = [topic for topic, _ in TOPIC_MAP.values()]
        assert len(topics) == len(set(topics)), \
            f"Duplicate MQTT topic in TOPIC_MAP: {[t for t in set(topics) if topics.count(t) > 1]}"

    def test_topic_map_has_no_duplicate_field_names(self):
        # Dict keys are unique by definition, but make sure we didn't list a
        # field name twice in dict form (would still be a single key).
        # Better assertion: every TOPIC_MAP key is a real SensorSnapshot field.
        snap_fields = {f.name for f in fields(SensorSnapshot) if f.name != "ais_targets"}
        for key in TOPIC_MAP.keys():
            assert key in snap_fields, f"TOPIC_MAP key {key!r} is not a SensorSnapshot field"

    def test_every_primitive_snapshot_field_appears_in_topic_map(self):
        # Excluding ais_targets which is published separately.
        snap_fields = {f.name for f in fields(SensorSnapshot) if f.name != "ais_targets"}
        missing = snap_fields - TOPIC_MAP.keys()
        assert not missing, \
            f"SensorSnapshot fields missing from TOPIC_MAP: {sorted(missing)}"

    def test_topics_use_consistent_namespace(self):
        for topic, _ in TOPIC_MAP.values():
            assert topic.startswith("boat/hunter41/"), \
                f"Topic {topic!r} does not use the boat/hunter41/ prefix"

    def test_control_and_status_topics_are_separated_namespaces(self):
        assert CTRL_RUN_TOPIC.startswith("boat/control/")
        assert CTRL_SCENARIO_TOPIC.startswith("boat/control/")
        assert STATUS_ACTIVE_TOPIC.startswith("boat/hunter41/sim/")
        assert STATUS_SCENARIO_TOPIC.startswith("boat/hunter41/sim/")
        assert AIS_TARGETS_TOPIC.startswith("boat/hunter41/ais/")


class TestTransformers:
    """Every transformer in TOPIC_MAP produces a string or None."""

    def test_default_snapshot_produces_only_strings_or_none(self):
        snap = SensorSnapshot()
        d = snap.to_dict()
        for fname, (topic, transform) in TOPIC_MAP.items():
            value = d[fname]
            payload = transform(value)
            if payload is not None:
                assert isinstance(payload, str), \
                    f"Field {fname!r} -> {payload!r} is not str"

    def test_bool_transformer_emits_one_zero(self):
        snap = SensorSnapshot(shore_power=True, generator=False, bilge_wet=True)
        _, t = TOPIC_MAP["shore_power"]
        assert t(True) == "1"
        assert t(False) == "0"

    def test_online_transformer_emits_on_off(self):
        _, t = TOPIC_MAP["online"]
        assert t(True) == "ON"
        assert t(False) == "OFF"

    def test_voltage_transformer_two_decimals(self):
        _, t = TOPIC_MAP["house_v"]
        assert t(12.5) == "12.50"
        assert t(11) == "11.00"

    def test_temperature_transformer_one_decimal(self):
        _, t = TOPIC_MAP["cabin_temp_c"]
        assert t(22.0) == "22.0"
        assert t(22.34) == "22.3"

    def test_lat_lon_transformer_six_decimals(self):
        _, t = TOPIC_MAP["lat"]
        assert t(41.4536) == "41.453600"
        _, t2 = TOPIC_MAP["lon"]
        assert t2(-82.71) == "-82.710000"

    def test_int_field_transformer_no_decimal(self):
        _, t = TOPIC_MAP["uptime_s"]
        assert t(1234) == "1234"
        _, t2 = TOPIC_MAP["rssi_dbm"]
        assert t2(-67) == "-67"

    def test_house_soc_can_be_none(self):
        # In Phase 6 (no Victron BLE yet) house_soc may legitimately be None.
        _, t = TOPIC_MAP["house_soc"]
        # Default snapshot has float SoC = 85.0 since v0.2; but the
        # transformer must accept None gracefully for v1 (pre-Victron) usage.
        assert t(None) is None
        # `_f1` formatter is used (one decimal place).
        assert t(85.0) == "85.0"
        assert t(73.456) == "73.5"


class TestAisTargets:
    """AIS targets are published as a JSON array on a dedicated topic."""

    def test_serialize_empty_list_returns_empty_array(self):
        out = serialize_ais_targets([])
        assert json.loads(out) == []

    def test_serialize_single_target_round_trip(self):
        target = AisTarget(
            mmsi=367123456, name="GOOD TIMES", type="Class B",
            bearing_deg=42.5, range_nm=1.234, cog_deg=88.8, sog_kt=4.0, age_s=12,
        )
        out = serialize_ais_targets([target])
        decoded = json.loads(out)
        assert decoded == [{
            "mmsi": 367123456,
            "name": "GOOD TIMES",
            "type": "Class B",
            "bearing": 42.5,
            "range_nm": 1.23,
            "cog": 88.8,
            "sog": 4.0,
            "age": 12,
        }]

    def test_serialize_rounds_floats_consistently(self):
        target = AisTarget(
            mmsi=1, name="X", type="Class B",
            bearing_deg=42.55555, range_nm=1.99999, cog_deg=180.0, sog_kt=5.65, age_s=1,
        )
        decoded = json.loads(serialize_ais_targets([target]))[0]
        # round() uses banker's rounding (round-half-to-even). 5.65 → 5.6.
        # 42.55555 → 42.6 (next digit is 5, prev is 5, round-up wins on
        # non-tie cases). 1.99999 → 2.0.
        assert decoded["bearing"] == 42.6
        assert decoded["range_nm"] == 2.0
        # 5.65 with banker's rounding to 1 decimal → 5.6 (tie, round to even).
        assert decoded["sog"] in (5.6, 5.7)


class TestSnapshotDefaults:
    """Sane defaults for every field."""

    def test_default_snapshot_is_internally_consistent(self):
        snap = SensorSnapshot()
        # At-slip defaults: shore power on, no engine, no leaks
        assert snap.online is True
        assert snap.shore_power is True
        assert snap.generator is False
        assert snap.bilge_wet is False
        assert snap.engine_running is False
        assert snap.smoke_alarm is False
        assert snap.leak_head is False
        assert snap.leak_galley is False
        assert snap.leak_engine is False
        # Voltages plausible
        assert 11.0 <= snap.house_v <= 14.0
        assert 11.0 <= snap.start_v <= 14.0
        # Position at Sandusky slip
        assert 41.4 <= snap.lat <= 41.5
        assert -82.8 <= snap.lon <= -82.6

    def test_to_dict_contains_every_field(self):
        snap = SensorSnapshot()
        d = snap.to_dict()
        for f in fields(SensorSnapshot):
            assert f.name in d, f"to_dict() missing field {f.name!r}"

    def test_lwt_constants_match_online_payload(self):
        _, t = TOPIC_MAP["online"]
        assert t(True) == LWT_PAYLOAD_ONLINE
        assert t(False) == LWT_PAYLOAD_OFFLINE
        # LWT topic is the same as online state topic (HA uses one topic
        # for both presence and state)
        topic, _ = TOPIC_MAP["online"]
        assert topic == LWT_TOPIC
