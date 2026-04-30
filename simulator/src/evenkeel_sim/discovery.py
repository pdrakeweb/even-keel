"""Home Assistant MQTT discovery payload generator (v0.2 expanded)."""
from __future__ import annotations

from typing import Iterable

from .sensors import TOPIC_MAP

DEVICE = {
    "identifiers": ["evenkeel_boatmon_1"],
    "name": "Boat",                  # short name → entity_id slugs become 'boat_*'
    "model": "EvenKeel v1",
    "manufacturer": "EvenKeel (DIY)",
    "sw_version": "0.2.0-sim",
}

# Per-field metadata. Component, label, device_class, unit, state_class.
META: dict[str, dict] = {
    # Status
    "online":              {"component": "binary_sensor", "name": "Online",                   "device_class": "connectivity", "payload_on": "ON", "payload_off": "OFF"},
    # Power
    "shore_power":         {"component": "binary_sensor", "name": "Shore power",              "device_class": "plug",          "payload_on": "1", "payload_off": "0"},
    "shore_v":             {"component": "sensor",        "name": "Shore voltage",            "device_class": "voltage", "unit": "V", "state_class": "measurement"},
    "shore_a":             {"component": "sensor",        "name": "Shore current",            "device_class": "current", "unit": "A", "state_class": "measurement"},
    "generator":           {"component": "binary_sensor", "name": "Generator running",        "device_class": "running",       "payload_on": "1", "payload_off": "0"},
    "gen_v":               {"component": "sensor",        "name": "Generator voltage",        "device_class": "voltage", "unit": "V", "state_class": "measurement"},
    "gen_runtime_h":       {"component": "sensor",        "name": "Generator runtime",        "unit": "h", "state_class": "total_increasing", "icon": "mdi:engine-outline"},
    "power_source":        {"component": "sensor",        "name": "Power source",             "icon": "mdi:flash"},
    "house_v":             {"component": "sensor",        "name": "House battery V",          "device_class": "voltage", "unit": "V", "state_class": "measurement"},
    "house_a":             {"component": "sensor",        "name": "House battery A",          "device_class": "current", "unit": "A", "state_class": "measurement"},
    "house_soc":           {"component": "sensor",        "name": "House battery SoC",        "device_class": "battery", "unit": "%", "state_class": "measurement"},
    "house_ttg_min":       {"component": "sensor",        "name": "House battery time to go", "unit": "min", "state_class": "measurement", "icon": "mdi:timer-outline"},
    "start_v":             {"component": "sensor",        "name": "Start battery V",          "device_class": "voltage", "unit": "V", "state_class": "measurement"},
    "solar_v":             {"component": "sensor",        "name": "Solar panel V",            "device_class": "voltage", "unit": "V", "state_class": "measurement"},
    "solar_a":             {"component": "sensor",        "name": "Solar panel A",            "device_class": "current", "unit": "A", "state_class": "measurement"},
    "solar_w":             {"component": "sensor",        "name": "Solar power",              "device_class": "power", "unit": "W", "state_class": "measurement"},
    "solar_today_kwh":     {"component": "sensor",        "name": "Solar today",              "device_class": "energy", "unit": "kWh", "state_class": "total_increasing"},
    # Bilge
    "bilge_wet":           {"component": "binary_sensor", "name": "Bilge water detected",     "device_class": "moisture",      "payload_on": "1", "payload_off": "0"},
    "bilge_pump_cycles_today": {"component": "sensor",    "name": "Bilge pump cycles today",  "state_class": "total_increasing", "icon": "mdi:pump"},
    # Temperatures
    "cabin_temp_c":        {"component": "sensor", "name": "Cabin temperature",        "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "v_berth_temp_c":      {"component": "sensor", "name": "V-berth temperature",      "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "head_temp_c":         {"component": "sensor", "name": "Head temperature",         "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "galley_temp_c":       {"component": "sensor", "name": "Galley temperature",       "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "nav_temp_c":          {"component": "sensor", "name": "Nav station temperature",  "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "engine_temp_c":       {"component": "sensor", "name": "Engine bay temperature",   "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "engine_air_temp_c":   {"component": "sensor", "name": "Engine intake air temp",   "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "fridge_temp_c":       {"component": "sensor", "name": "Refrigerator",             "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "freezer_temp_c":      {"component": "sensor", "name": "Freezer",                  "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "lazarette_temp_c":    {"component": "sensor", "name": "Lazarette temperature",    "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    # Atmospherics
    "cabin_humidity_pct":  {"component": "sensor", "name": "Cabin humidity",           "device_class": "humidity", "unit": "%", "state_class": "measurement"},
    "cabin_pressure_hpa":  {"component": "sensor", "name": "Cabin pressure",           "device_class": "atmospheric_pressure", "unit": "hPa", "state_class": "measurement"},
    # Safety
    "co_ppm":              {"component": "sensor",        "name": "CO concentration",  "device_class": "carbon_monoxide", "unit": "ppm", "state_class": "measurement"},
    "smoke_alarm":         {"component": "binary_sensor", "name": "Smoke alarm",       "device_class": "smoke",   "payload_on": "1", "payload_off": "0"},
    "leak_head":           {"component": "binary_sensor", "name": "Head leak",         "device_class": "moisture","payload_on": "1", "payload_off": "0"},
    "leak_galley":         {"component": "binary_sensor", "name": "Galley leak",       "device_class": "moisture","payload_on": "1", "payload_off": "0"},
    "leak_engine":         {"component": "binary_sensor", "name": "Engine leak",       "device_class": "moisture","payload_on": "1", "payload_off": "0"},
    # Engine
    "engine_running":      {"component": "binary_sensor", "name": "Engine running",    "device_class": "running", "payload_on": "1", "payload_off": "0"},
    "engine_rpm":          {"component": "sensor",        "name": "Engine RPM",        "unit": "rpm", "state_class": "measurement", "icon": "mdi:engine"},
    "engine_oil_pressure_kpa": {"component": "sensor",    "name": "Engine oil pressure","unit": "kPa", "state_class": "measurement", "device_class": "pressure"},
    "engine_coolant_c":    {"component": "sensor",        "name": "Engine coolant",    "device_class": "temperature", "unit": "°C", "state_class": "measurement"},
    "engine_alt_v":        {"component": "sensor",        "name": "Alternator V",      "device_class": "voltage", "unit": "V", "state_class": "measurement"},
    "engine_runtime_h":    {"component": "sensor",        "name": "Engine hours",      "unit": "h", "state_class": "total_increasing", "icon": "mdi:engine"},
    # Tanks
    "fresh_water_pct":     {"component": "sensor", "name": "Fresh water",   "unit": "%", "state_class": "measurement", "icon": "mdi:water"},
    "holding_pct":         {"component": "sensor", "name": "Holding tank",  "unit": "%", "state_class": "measurement", "icon": "mdi:emoticon-poop"},
    "fuel_pct":            {"component": "sensor", "name": "Fuel",          "unit": "%", "state_class": "measurement", "icon": "mdi:fuel"},
    # Health
    "rssi_dbm":            {"component": "sensor", "name": "WiFi RSSI", "device_class": "signal_strength", "unit": "dBm", "state_class": "measurement", "entity_category": "diagnostic"},
    "uptime_s":            {"component": "sensor", "name": "Uptime",     "unit": "s", "state_class": "total_increasing", "entity_category": "diagnostic"},
    # Position
    "lat":                 {"component": "sensor", "name": "Latitude",  "icon": "mdi:latitude"},
    "lon":                 {"component": "sensor", "name": "Longitude", "icon": "mdi:longitude"},
    "sog_kt":              {"component": "sensor", "name": "Speed over ground",      "unit": "kn", "state_class": "measurement", "icon": "mdi:speedometer"},
    "cog_deg":             {"component": "sensor", "name": "Course over ground",     "unit": "°",  "state_class": "measurement", "icon": "mdi:compass"},
    "heading_deg":         {"component": "sensor", "name": "Heading",                "unit": "°",  "state_class": "measurement", "icon": "mdi:compass-outline"},
    "depth_m":             {"component": "sensor", "name": "Depth",                  "unit": "m",  "state_class": "measurement", "icon": "mdi:waves-arrow-down"},
    "speed_through_water_kt": {"component": "sensor", "name": "Speed through water", "unit": "kn", "state_class": "measurement", "icon": "mdi:speedometer-medium"},
    # Sailing
    "wind_apparent_kt":    {"component": "sensor", "name": "Apparent wind speed",    "unit": "kn", "state_class": "measurement", "icon": "mdi:weather-windy"},
    "wind_apparent_deg":   {"component": "sensor", "name": "Apparent wind angle",    "unit": "°",  "state_class": "measurement", "icon": "mdi:compass-outline"},
    "wind_true_kt":        {"component": "sensor", "name": "True wind speed",        "unit": "kn", "state_class": "measurement", "icon": "mdi:weather-windy"},
    "wind_true_deg":       {"component": "sensor", "name": "True wind direction",    "unit": "°",  "state_class": "measurement", "icon": "mdi:compass-outline"},
    "heel_deg":            {"component": "sensor", "name": "Heel",                   "unit": "°",  "state_class": "measurement", "icon": "mdi:angle-acute"},
    "pitch_deg":           {"component": "sensor", "name": "Pitch",                  "unit": "°",  "state_class": "measurement", "icon": "mdi:angle-obtuse"},
    # Anchor / geofence
    "anchor_armed":        {"component": "binary_sensor", "name": "Anchor armed",    "icon": "mdi:anchor", "payload_on": "1", "payload_off": "0"},
    "anchor_distance_m":   {"component": "sensor", "name": "Anchor distance",        "unit": "m",  "state_class": "measurement", "icon": "mdi:map-marker-distance"},
    "slip_distance_m":     {"component": "sensor", "name": "Slip distance",          "unit": "m",  "state_class": "measurement", "icon": "mdi:map-marker"},
    # Contacts
    "forepeak_hatch_open": {"component": "binary_sensor", "name": "Forepeak hatch",  "device_class": "door", "payload_on": "1", "payload_off": "0"},
    "main_hatch_open":     {"component": "binary_sensor", "name": "Main hatch",      "device_class": "door", "payload_on": "1", "payload_off": "0"},
    "lazarette_hatch_open":{"component": "binary_sensor", "name": "Lazarette hatch", "device_class": "door", "payload_on": "1", "payload_off": "0"},
    # AIS rollup
    "ais_targets_in_range": {"component": "sensor", "name": "AIS targets in range",  "icon": "mdi:radar", "state_class": "measurement"},
    "ais_nearest_name":     {"component": "sensor", "name": "Nearest AIS vessel",    "icon": "mdi:ship-wheel"},
    "ais_nearest_range_nm": {"component": "sensor", "name": "Nearest AIS range",     "unit": "nmi", "state_class": "measurement", "icon": "mdi:map-marker-distance"},
}


def build_discovery_payloads() -> Iterable[tuple[str, dict]]:
    for fname, (state_topic, _transform) in TOPIC_MAP.items():
        meta = META.get(fname, {})
        component = meta.get("component", "sensor")
        unique_id = f"evenkeel_boatmon_{fname}"
        config_topic = f"homeassistant/{component}/{unique_id}/config"
        # NB: deliberately NO `object_id`. With object_id set, HA uses
        # it verbatim as the entity_id slug (binary_sensor.<object_id>).
        # Without it, HA derives entity_id from device.name + name,
        # which gives binary_sensor.boat_bilge_water_detected — which is
        # what home-assistant/packages/boat_health.yaml templates
        # reference. unique_id stays stable so Pete's existing HA
        # registry isn't disturbed.
        payload = {
            "name": meta.get("name", fname),
            "unique_id": unique_id,
            "state_topic": state_topic,
            "device": DEVICE,
            "availability_topic": "boat/hunter41/status/online",
            "payload_available": "ON",
            "payload_not_available": "OFF",
        }
        for opt_key, payload_key in [
            ("device_class", "device_class"),
            ("unit", "unit_of_measurement"),
            ("state_class", "state_class"),
            ("icon", "icon"),
            ("entity_category", "entity_category"),
            ("payload_on", "payload_on"),
            ("payload_off", "payload_off"),
        ]:
            if opt_key in meta:
                payload[payload_key] = meta[opt_key]
        yield config_topic, payload

    # Boat tracker (device_tracker entity for HA map card).
    # No object_id here either — HA derives device_tracker.boat_boat
    # which we leave alone; renaming it forces breaking changes in
    # consumers that already reference the existing entity_id.
    yield "homeassistant/device_tracker/evenkeel_boat/config", {
        "name": "Boat",
        "unique_id": "evenkeel_boat_tracker",
        "state_topic": "boat/hunter41/tracker/state",
        "json_attributes_topic": "boat/hunter41/tracker/attrs",
        "source_type": "gps",
        "device": DEVICE,
        "icon": "mdi:sail-boat",
    }
