"""Canonical sensor data model and MQTT topic mapping.

Single source of truth for what the simulator publishes. The real
ESP32 firmware publishes the same topic tree.

v0.2: expanded sensor set per user feedback — AIS targets list, GPS
heading, shore voltage/current, freezer + multi-zone temperatures,
engine RPM/oil/coolant/fuel, tanks (fresh/holding/fuel), wind speed
and direction, depth, heel, anchor distance, hatch contacts, water
leak sensors, solar.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class AisTarget:
    mmsi: int
    name: str
    type: str           # 'Class A' | 'Class B' | 'Pax' | 'Cargo' | 'Fishing' | ...
    bearing_deg: float
    range_nm: float
    cog_deg: float
    sog_kt: float
    age_s: int


@dataclass
class SensorSnapshot:
    """One full picture of boat state. Every primitive field maps to one
    MQTT topic via TOPIC_MAP. AIS targets are published as a single JSON
    array on a dedicated topic for the dashboard's iteration cards.
    """
    # ─── Status ──────────────────────────────────────────────
    online: bool = True

    # ─── Power ───────────────────────────────────────────────
    shore_power: bool = True
    shore_v: float = 120.0          # AC volts (0 when not on shore)
    shore_a: float = 4.5            # AC amps drawn from shore
    generator: bool = False
    gen_v: float = 0.0
    gen_runtime_h: float = 1284.5
    power_source: str = "shore"     # 'shore' | 'generator' | 'battery'

    house_v: float = 12.7
    house_a: float = -2.5           # negative = discharging
    house_soc: float = 85.0
    house_ttg_min: int = 1200       # time-to-go minutes
    start_v: float = 12.5

    solar_v: float = 18.6
    solar_a: float = 4.2
    solar_w: float = 78.1
    solar_today_kwh: float = 1.45

    # ─── Bilge ───────────────────────────────────────────────
    bilge_wet: bool = False
    bilge_pump_cycles_today: int = 2

    # ─── Temperatures (multi-zone) ───────────────────────────
    cabin_temp_c: float = 22.0
    v_berth_temp_c: float = 21.0
    head_temp_c: float = 21.5
    galley_temp_c: float = 22.5
    nav_temp_c: float = 22.0
    engine_temp_c: float = 20.0
    engine_air_temp_c: float = 28.0
    fridge_temp_c: float = 4.0
    freezer_temp_c: float = -16.0
    lazarette_temp_c: float = 18.0

    # ─── Cabin atmospherics (BME280) ─────────────────────────
    cabin_humidity_pct: float = 55.0
    cabin_pressure_hpa: float = 1013.0

    # ─── CO / smoke / leak (Tier 5b Zigbee) ─────────────────
    co_ppm: float = 0.0
    smoke_alarm: bool = False
    leak_head: bool = False
    leak_galley: bool = False
    leak_engine: bool = False

    # ─── Engine (J1939 / Tier 6) ────────────────────────────
    engine_running: bool = False
    engine_rpm: int = 0
    engine_oil_pressure_kpa: float = 0.0
    engine_coolant_c: float = 60.0
    engine_alt_v: float = 13.8
    engine_runtime_h: float = 632.5

    # ─── Tanks (% full) ──────────────────────────────────────
    fresh_water_pct: float = 78.0
    holding_pct: float = 22.0
    fuel_pct: float = 64.0

    # ─── Health ──────────────────────────────────────────────
    rssi_dbm: int = -65
    uptime_s: int = 0

    # ─── Position (NMEA 2000 / GPS) ──────────────────────────
    lat: float = 41.4536
    lon: float = -82.7100
    sog_kt: float = 0.0
    cog_deg: float = 0.0
    heading_deg: float = 0.0        # magnetic heading from autopilot
    depth_m: float = 8.4
    speed_through_water_kt: float = 0.0

    # ─── Sailing (NMEA 2000) ─────────────────────────────────
    wind_apparent_kt: float = 0.0
    wind_apparent_deg: float = 0.0  # AWA (relative to bow)
    wind_true_kt: float = 0.0
    wind_true_deg: float = 0.0      # TWD (relative to true north)
    heel_deg: float = 0.0           # +ve = starboard
    pitch_deg: float = 0.0

    # ─── Anchor / Geofence (Phase 9) ─────────────────────────
    anchor_armed: bool = False
    anchor_distance_m: float = 0.0  # distance from armed anchor point
    slip_distance_m: float = 0.0    # distance from slip A-14

    # ─── Hatches / contacts (Tier 5b Zigbee) ────────────────
    forepeak_hatch_open: bool = False
    main_hatch_open: bool = True
    lazarette_hatch_open: bool = False

    # ─── AIS rollup + targets ────────────────────────────────
    ais_targets_in_range: int = 0
    ais_nearest_name: str = ""
    ais_nearest_range_nm: float = 0.0
    ais_targets: list[AisTarget] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for f in fields(self):
            v = getattr(self, f.name)
            if f.name == "ais_targets":
                d[f.name] = [
                    {"mmsi": t.mmsi, "name": t.name, "type": t.type,
                     "bearing": t.bearing_deg, "range_nm": t.range_nm,
                     "cog": t.cog_deg, "sog": t.sog_kt, "age": t.age_s}
                    for t in v
                ]
            else:
                d[f.name] = v
        return d


# ─── Mapping from primitive field → MQTT topic + transformer ──────────
def _f1(v):  return f"{v:.1f}" if v is not None else None
def _f2(v):  return f"{v:.2f}" if v is not None else None
def _f6(v):  return f"{v:.6f}" if v is not None else None
def _bool(v): return "1" if v else "0"
def _on_off(v): return "ON" if v else "OFF"
def _int(v):  return str(int(v))

TOPIC_MAP: dict[str, tuple[str, Any]] = {
    "online":              ("boat/hunter41/status/online",                _on_off),
    # Power
    "shore_power":         ("boat/hunter41/power/shore",                  _bool),
    "shore_v":             ("boat/hunter41/power/shore/v",                _f1),
    "shore_a":             ("boat/hunter41/power/shore/a",                _f1),
    "generator":           ("boat/hunter41/power/generator",              _bool),
    "gen_v":               ("boat/hunter41/power/generator/v",            _f1),
    "gen_runtime_h":       ("boat/hunter41/power/generator/runtime_h",    _f1),
    "power_source":        ("boat/hunter41/power/source",                 str),
    "house_v":             ("boat/hunter41/power/battery/house/v",        _f2),
    "house_a":             ("boat/hunter41/power/battery/house/a",        _f2),
    "house_soc":           ("boat/hunter41/power/battery/house/soc",      _f1),
    "house_ttg_min":       ("boat/hunter41/power/battery/house/ttg_min",  _int),
    "start_v":             ("boat/hunter41/power/battery/start/v",        _f2),
    "solar_v":             ("boat/hunter41/power/solar/v",                _f1),
    "solar_a":             ("boat/hunter41/power/solar/a",                _f1),
    "solar_w":             ("boat/hunter41/power/solar/w",                _f1),
    "solar_today_kwh":     ("boat/hunter41/power/solar/today_kwh",        _f2),
    # Bilge
    "bilge_wet":           ("boat/hunter41/bilge/water_detected",         _bool),
    "bilge_pump_cycles_today": ("boat/hunter41/bilge/pump_cycles_today",  _int),
    # Temperatures
    "cabin_temp_c":        ("boat/hunter41/temp/cabin",                   _f1),
    "v_berth_temp_c":      ("boat/hunter41/temp/v_berth",                 _f1),
    "head_temp_c":         ("boat/hunter41/temp/head",                    _f1),
    "galley_temp_c":       ("boat/hunter41/temp/galley",                  _f1),
    "nav_temp_c":          ("boat/hunter41/temp/nav_station",             _f1),
    "engine_temp_c":       ("boat/hunter41/temp/engine_compartment",      _f1),
    "engine_air_temp_c":   ("boat/hunter41/temp/engine_intake_air",       _f1),
    "fridge_temp_c":       ("boat/hunter41/temp/refrigerator",            _f1),
    "freezer_temp_c":      ("boat/hunter41/temp/freezer",                 _f1),
    "lazarette_temp_c":    ("boat/hunter41/temp/lazarette",               _f1),
    # Atmospherics
    "cabin_humidity_pct":  ("boat/hunter41/cabin/humidity",               _f1),
    "cabin_pressure_hpa":  ("boat/hunter41/cabin/pressure",               _f1),
    # Safety
    "co_ppm":              ("boat/hunter41/safety/co_ppm",                _f1),
    "smoke_alarm":         ("boat/hunter41/safety/smoke",                 _bool),
    "leak_head":           ("boat/hunter41/leak/head",                    _bool),
    "leak_galley":         ("boat/hunter41/leak/galley",                  _bool),
    "leak_engine":         ("boat/hunter41/leak/engine",                  _bool),
    # Engine
    "engine_running":      ("boat/hunter41/engine/running",               _bool),
    "engine_rpm":          ("boat/hunter41/engine/rpm",                   _int),
    "engine_oil_pressure_kpa": ("boat/hunter41/engine/oil_pressure",      _f1),
    "engine_coolant_c":    ("boat/hunter41/engine/coolant",               _f1),
    "engine_alt_v":        ("boat/hunter41/engine/alternator_v",          _f1),
    "engine_runtime_h":    ("boat/hunter41/engine/runtime_h",             _f1),
    # Tanks
    "fresh_water_pct":     ("boat/hunter41/tanks/fresh_water",            _f1),
    "holding_pct":         ("boat/hunter41/tanks/holding",                _f1),
    "fuel_pct":            ("boat/hunter41/tanks/fuel",                   _f1),
    # Health
    "rssi_dbm":            ("boat/hunter41/health/rssi",                  _int),
    "uptime_s":            ("boat/hunter41/health/uptime_s",              _int),
    # Position
    "lat":                 ("boat/hunter41/location/lat",                 _f6),
    "lon":                 ("boat/hunter41/location/lon",                 _f6),
    "sog_kt":              ("boat/hunter41/location/sog",                 _f2),
    "cog_deg":             ("boat/hunter41/location/cog",                 _f1),
    "heading_deg":         ("boat/hunter41/location/heading",             _f1),
    "depth_m":             ("boat/hunter41/location/depth",               _f1),
    "speed_through_water_kt": ("boat/hunter41/location/stw",              _f2),
    # Sailing
    "wind_apparent_kt":    ("boat/hunter41/wind/apparent_speed",          _f1),
    "wind_apparent_deg":   ("boat/hunter41/wind/apparent_angle",          _f1),
    "wind_true_kt":        ("boat/hunter41/wind/true_speed",              _f1),
    "wind_true_deg":       ("boat/hunter41/wind/true_direction",          _f1),
    "heel_deg":            ("boat/hunter41/motion/heel",                  _f1),
    "pitch_deg":           ("boat/hunter41/motion/pitch",                 _f1),
    # Anchor / Geofence
    "anchor_armed":        ("boat/hunter41/anchor/armed",                 _bool),
    "anchor_distance_m":   ("boat/hunter41/anchor/distance_m",            _f1),
    "slip_distance_m":     ("boat/hunter41/slip/distance_m",              _f1),
    # Contacts
    "forepeak_hatch_open": ("boat/hunter41/contact/forepeak_hatch",       _bool),
    "main_hatch_open":     ("boat/hunter41/contact/main_hatch",           _bool),
    "lazarette_hatch_open": ("boat/hunter41/contact/lazarette_hatch",     _bool),
    # AIS rollup
    "ais_targets_in_range": ("boat/hunter41/ais/targets_in_range",        _int),
    "ais_nearest_name":    ("boat/hunter41/ais/nearest_name",             str),
    "ais_nearest_range_nm": ("boat/hunter41/ais/nearest_range_nm",        _f2),
}

# AIS target list goes to its own topic as a JSON array.
AIS_TARGETS_TOPIC = "boat/hunter41/ais/targets"


def serialize_ais_targets(targets: list[AisTarget]) -> str:
    return json.dumps([
        {
            "mmsi": t.mmsi,
            "name": t.name,
            "type": t.type,
            "bearing": round(t.bearing_deg, 1),
            "range_nm": round(t.range_nm, 2),
            "cog": round(t.cog_deg, 1),
            "sog": round(t.sog_kt, 1),
            "age": t.age_s,
        }
        for t in targets
    ])


# ─── Control plane (HA → simulator) ───────────────────────────────────
CTRL_RUN_TOPIC = "boat/control/simulator/run"
CTRL_SCENARIO_TOPIC = "boat/control/simulator/scenario"

# ─── Status (simulator → HA) ──────────────────────────────────────────
STATUS_ACTIVE_TOPIC = "boat/hunter41/sim/active"
STATUS_SCENARIO_TOPIC = "boat/hunter41/sim/scenario"

# ─── LWT ──────────────────────────────────────────────────────────────
LWT_TOPIC = "boat/hunter41/status/online"
LWT_PAYLOAD_OFFLINE = "OFF"
LWT_PAYLOAD_ONLINE = "ON"
