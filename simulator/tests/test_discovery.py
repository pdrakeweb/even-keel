"""Discovery payload contract tests.

Home Assistant MQTT discovery is the contract between the simulator and HA.
Every primitive sensor in TOPIC_MAP must have a discovery payload that:
- Has unique_id, state_topic, device, availability_topic
- Has a valid HA `component` (sensor / binary_sensor)
- Survives JSON round-trip (no non-serializable objects)
- Uses an availability topic that matches the online state topic
- Declares a device_class only from HA's known set (where applicable)
"""
from __future__ import annotations

import json

import pytest

from evenkeel_sim.discovery import DEVICE, META, build_discovery_payloads
from evenkeel_sim.sensors import TOPIC_MAP


REQUIRED_PAYLOAD_KEYS = {
    "name", "unique_id", "state_topic", "device",
    "availability_topic", "payload_available", "payload_not_available",
}

# HA's standard device_class names for the kinds of sensors we publish.
KNOWN_DEVICE_CLASSES = {
    "voltage", "current", "battery", "temperature", "humidity",
    "atmospheric_pressure", "pressure", "energy", "power",
    "signal_strength", "carbon_monoxide", "smoke", "moisture",
    "plug", "running", "connectivity", "door", "problem",
}


def _payloads():
    """Materialize every (topic, payload) tuple."""
    return list(build_discovery_payloads())


class TestPayloadShape:
    def test_payloads_emitted_for_every_field(self):
        # +1 for the device_tracker that's separate from TOPIC_MAP
        payloads = _payloads()
        assert len(payloads) == len(TOPIC_MAP) + 1, \
            f"Expected {len(TOPIC_MAP) + 1} payloads (TOPIC_MAP + device_tracker), got {len(payloads)}"

    def test_every_payload_has_required_keys(self):
        # device_tracker is special-cased (no availability_topic — HA's
        # device_tracker schema doesn't include it in this MQTT discovery
        # variant). Tracker is verified in TestDeviceTracker below.
        for topic, payload in _payloads():
            if "device_tracker" in topic:
                continue
            missing = REQUIRED_PAYLOAD_KEYS - payload.keys()
            assert not missing, f"{topic}: missing required keys {missing}"

    def test_every_unique_id_is_unique(self):
        ids = [p["unique_id"] for _, p in _payloads()]
        assert len(ids) == len(set(ids)), \
            f"Duplicate unique_id: {[i for i in set(ids) if ids.count(i) > 1]}"

    def test_every_payload_is_json_serializable(self):
        for topic, payload in _payloads():
            try:
                json.dumps(payload)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Payload for {topic} not JSON-serializable: {e}")

    def test_config_topic_format(self):
        for topic, _ in _payloads():
            # homeassistant/<component>/<unique_id>/config
            parts = topic.split("/")
            assert parts[0] == "homeassistant"
            assert parts[-1] == "config"
            assert parts[1] in {"sensor", "binary_sensor", "device_tracker"}, \
                f"{topic}: unexpected component {parts[1]}"


class TestDeviceMetadata:
    def test_device_block_has_required_fields(self):
        assert "identifiers" in DEVICE
        assert "name" in DEVICE
        assert isinstance(DEVICE["identifiers"], list)
        assert len(DEVICE["identifiers"]) >= 1

    def test_device_name_is_short_for_clean_entity_ids(self):
        # HA derives entity_id from device.name + entity.name. We want
        # entity_ids like `sensor.boat_house_battery_v`, NOT
        # `sensor.hunter_41ds_boatmon_house_battery_v`.
        # Lesson learned the hard way during development.
        assert DEVICE["name"] == "Boat", \
            f"Device name {DEVICE['name']!r} will produce verbose entity_ids"

    def test_every_payload_references_same_device(self):
        for _, payload in _payloads():
            assert payload["device"]["identifiers"] == DEVICE["identifiers"], \
                f"Payload {payload['unique_id']} references wrong device"


class TestDeviceClasses:
    """Where set, device_class must be one of HA's recognized values."""

    @pytest.mark.parametrize("field_name,meta", list(META.items()))
    def test_device_class_is_valid(self, field_name, meta):
        if "device_class" not in meta:
            pytest.skip(f"{field_name}: no device_class set")
        assert meta["device_class"] in KNOWN_DEVICE_CLASSES, \
            f"{field_name}: unknown device_class {meta['device_class']}"


class TestAvailability:
    """Availability uses the LWT topic so HA can show entities offline."""

    def test_availability_topic_is_online_state_topic(self):
        for topic, payload in _payloads():
            if "device_tracker" in topic:
                continue
            assert payload["availability_topic"] == "boat/hunter41/status/online", \
                f"{topic}: wrong availability_topic"

    def test_payload_available_is_ON(self):
        for topic, payload in _payloads():
            if "device_tracker" in topic:
                continue
            assert payload["payload_available"] == "ON"

    def test_payload_not_available_is_OFF(self):
        for topic, payload in _payloads():
            if "device_tracker" in topic:
                continue
            assert payload["payload_not_available"] == "OFF"


class TestStateTopicCoherence:
    """The state_topic in each payload must match TOPIC_MAP."""

    def test_state_topic_matches_topic_map(self):
        # TOPIC_MAP[field][0] is the topic. Each discovery payload's
        # state_topic must equal that.
        payloads = {p["unique_id"]: p for _, p in _payloads()}
        for fname, (topic, _) in TOPIC_MAP.items():
            unique_id = f"evenkeel_boatmon_{fname}"
            assert unique_id in payloads, f"No discovery for {fname}"
            assert payloads[unique_id]["state_topic"] == topic, \
                f"{fname}: discovery state_topic mismatch"


class TestBinarySensorPayloads:
    """binary_sensor entries need payload_on / payload_off."""

    def test_binary_sensors_declare_on_off_payloads(self):
        for topic, payload in _payloads():
            if topic.startswith("homeassistant/binary_sensor/"):
                assert "payload_on" in payload, f"{topic}: binary_sensor missing payload_on"
                assert "payload_off" in payload, f"{topic}: binary_sensor missing payload_off"


class TestDeviceTracker:
    """Special-case the device_tracker entity that drives the HA map card."""

    def test_device_tracker_published(self):
        payloads = _payloads()
        trackers = [p for t, p in payloads if "device_tracker" in t]
        assert len(trackers) == 1, "Expected exactly one device_tracker"

    def test_device_tracker_uses_attributes_topic(self):
        payloads = _payloads()
        for topic, p in payloads:
            if "device_tracker" in topic:
                assert "json_attributes_topic" in p
                assert p["json_attributes_topic"] == "boat/hunter41/tracker/attrs"
                assert p["state_topic"] == "boat/hunter41/tracker/state"
