"""Scenario engine — v0.2 with the expanded sensor set."""
from __future__ import annotations

import math
import random
from dataclasses import replace
from typing import Callable, Iterable

from .generators import (
    Transient,
    fridge_cycle,
    gps_drift_around,
    gps_track,
    jittered,
    linear_ramp,
    slow_drift,
)
from .sensors import AisTarget, SensorSnapshot

ScenarioFn = Callable[[float, SensorSnapshot, random.Random], SensorSnapshot]

SLIP_LAT = 41.4536
SLIP_LON = -82.7100


# ─── AIS fleet helpers ────────────────────────────────────────────────
_AIS_FLEET = [
    ("GOOD TIMES",       "Class B",  367123456),
    ("PELEE ISL FERRY",  "Pax",      366914420),
    ("CSL STEELHEAD",    "Cargo",    366998211),
    ("WALLEYE HUNTER",   "Fishing",  367553310),
    ("LAKE EXPRESS",     "Pax",      366512750),
    ("SAGINAW",          "Cargo",    367017840),
    ("BLACK PEARL",      "Class B",  367612300),
    ("ANCHOR DOWN",      "Class B",  367778822),
    ("MV WHITE STAR",    "Cargo",    366999111),
]


def _build_ais(rng: random.Random, count: int) -> tuple[list[AisTarget], str, float]:
    """Pick `count` random fleet members and assign positions."""
    if count <= 0:
        return [], "", 0.0
    pool = list(_AIS_FLEET)
    rng.shuffle(pool)
    picks = pool[:min(count, len(pool))]
    targets: list[AisTarget] = []
    for name, ttype, mmsi in picks:
        targets.append(AisTarget(
            mmsi=mmsi,
            name=name,
            type=ttype,
            bearing_deg=rng.uniform(0, 360),
            range_nm=round(abs(rng.gauss(2.5, 1.5)) + 0.3, 2),
            cog_deg=rng.uniform(0, 360),
            sog_kt=round(abs(rng.gauss(6, 4)), 1),
            age_s=rng.randint(2, 30),
        ))
    targets.sort(key=lambda t: t.range_nm)
    nearest = targets[0]
    return targets, nearest.name, nearest.range_nm


# ─── individual scenarios ─────────────────────────────────────────────

def _normal(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    """At slip on shore power. All systems healthy."""
    targets, nname, nrange = _build_ais(rng, 3)
    return SensorSnapshot(
        online=True,
        shore_power=True,
        shore_v=jittered(120.4, 0.5, rng=rng),
        shore_a=jittered(4.5, 0.4, rng=rng),
        generator=False,
        gen_v=0.0,
        gen_runtime_h=1284.5,
        power_source="shore",
        house_v=jittered(slow_drift(12.7, 600, 0.05, t), 0.02, rng=rng),
        house_a=jittered(-1.5, 0.4, rng=rng),
        house_soc=jittered(slow_drift(85, 1800, 5, t), 0.5, rng=rng),
        house_ttg_min=int(jittered(1200, 30, rng=rng)),
        start_v=jittered(12.6, 0.03, rng=rng),
        solar_v=jittered(18.6, 0.3, rng=rng),
        solar_a=jittered(slow_drift(4.2, 14400, 4, t), 0.15, rng=rng),
        solar_w=jittered(slow_drift(78, 14400, 70, t), 4, rng=rng),
        solar_today_kwh=round(1.45 + (t / 3600) * 0.05, 2),
        bilge_wet=False,
        bilge_pump_cycles_today=int(t // 3600) % 5,
        cabin_temp_c=jittered(slow_drift(22.0, 86400, 3.0, t), 0.15, rng=rng),
        v_berth_temp_c=jittered(21.0, 0.2, rng=rng),
        head_temp_c=jittered(21.5, 0.2, rng=rng),
        galley_temp_c=jittered(22.5, 0.2, rng=rng),
        nav_temp_c=jittered(22.0, 0.2, rng=rng),
        engine_temp_c=jittered(20.0, 0.2, rng=rng),
        engine_air_temp_c=jittered(28.0, 0.3, rng=rng),
        fridge_temp_c=fridge_cycle(t),
        freezer_temp_c=jittered(-16.0, 0.4, rng=rng),
        lazarette_temp_c=jittered(18.0, 0.3, rng=rng),
        cabin_humidity_pct=jittered(slow_drift(55, 86400, 8, t), 1.0, rng=rng),
        cabin_pressure_hpa=jittered(slow_drift(1013, 86400, 4, t), 0.2, rng=rng),
        co_ppm=jittered(0.0, 0.05, rng=rng),
        smoke_alarm=False,
        leak_head=False, leak_galley=False, leak_engine=False,
        engine_running=False,
        engine_rpm=0,
        engine_oil_pressure_kpa=0.0,
        engine_coolant_c=jittered(20, 0.3, rng=rng),
        engine_alt_v=0.0,
        engine_runtime_h=632.5,
        fresh_water_pct=jittered(78.0, 0.3, rng=rng),
        holding_pct=jittered(22.0, 0.3, rng=rng),
        fuel_pct=jittered(64.0, 0.2, rng=rng),
        rssi_dbm=int(jittered(-65, 4, rng=rng)),
        uptime_s=int(t),
        lat=SLIP_LAT,
        lon=SLIP_LON,
        sog_kt=0.0,
        cog_deg=0.0,
        heading_deg=jittered(225.0, 2.0, rng=rng),
        depth_m=jittered(8.4, 0.05, rng=rng),
        speed_through_water_kt=0.0,
        wind_apparent_kt=jittered(6.0, 1.5, rng=rng),
        wind_apparent_deg=jittered(135, 10, rng=rng),
        wind_true_kt=jittered(6.5, 1.5, rng=rng),
        wind_true_deg=jittered(220, 10, rng=rng),
        heel_deg=jittered(0.0, 0.5, rng=rng),
        pitch_deg=jittered(0.0, 0.3, rng=rng),
        anchor_armed=False,
        anchor_distance_m=0.0,
        slip_distance_m=jittered(2.0, 0.4, rng=rng),
        forepeak_hatch_open=False,
        main_hatch_open=True,
        lazarette_hatch_open=False,
        ais_targets_in_range=len(targets),
        ais_nearest_name=nname,
        ais_nearest_range_nm=nrange,
        ais_targets=targets,
    )


def _low_battery(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    base = _normal(t, prev, rng)
    if t < 600:
        v = linear_ramp(t, 0, 600, 12.6, 11.7)
        soc = linear_ramp(t, 0, 600, 85, 38)
        gen_on = False; src = "battery"; shore = False
    elif t < 1800:
        v = linear_ramp(t, 600, 1800, 11.7, 12.4)
        soc = linear_ramp(t, 600, 1800, 38, 72)
        gen_on = True; src = "generator"; shore = False
    else:
        v = jittered(12.6, 0.05, rng=rng)
        soc = jittered(78, 1, rng=rng)
        gen_on = False; src = "battery"; shore = False
    return replace(
        base,
        house_v=jittered(v, 0.04, rng=rng),
        house_soc=soc,
        house_a=jittered(-7.0 if not gen_on else 8.0, 1.0, rng=rng),
        shore_power=shore, shore_v=0.0, shore_a=0.0,
        generator=gen_on, gen_v=120.4 if gen_on else 0.0,
        power_source=src,
    )


def _bilge_wet(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    base = _normal(t, prev, rng)
    wet = Transient(start_s=30, end_s=120).active(t)
    return replace(base, bilge_wet=wet,
                   bilge_pump_cycles_today=base.bilge_pump_cycles_today + (1 if wet else 0))


def _shore_lost(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    base = _normal(t, prev, rng)
    if t < 15:
        return base
    sag_v = linear_ramp(t, 15, 900, 12.6, 12.0)
    return replace(
        base,
        shore_power=False, shore_v=0.0, shore_a=0.0,
        generator=False, gen_v=0.0,
        power_source="battery",
        house_v=jittered(sag_v, 0.03, rng=rng),
        house_a=jittered(-3.5, 0.4, rng=rng),
        house_soc=jittered(linear_ramp(t, 15, 900, 85, 70), 0.5, rng=rng),
    )


def _gen_running(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    base = _normal(t, prev, rng)
    chg_v = linear_ramp(t, 0, 1800, 11.9, 13.4)
    return replace(
        base,
        shore_power=False, shore_v=0.0, shore_a=0.0,
        generator=True, gen_v=jittered(120.5, 0.5, rng=rng),
        power_source="generator",
        house_v=jittered(chg_v, 0.04, rng=rng),
        house_a=jittered(12.0, 1.5, rng=rng),
        engine_temp_c=jittered(38.0, 0.5, rng=rng),
        gen_runtime_h=base.gen_runtime_h + t / 3600,
    )


def _anchor_drag(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    base = _normal(t, prev, rng)
    radius = 8 if t < 60 else 8 + (t - 60) * 0.8
    lat, lon = gps_drift_around(SLIP_LAT, SLIP_LON, radius, t, rng)
    distance = ((lat - SLIP_LAT) * 111_111) ** 2 + ((lon - SLIP_LON) * 111_111 * math.cos(math.radians(SLIP_LAT))) ** 2
    distance_m = math.sqrt(distance)
    return replace(
        base, lat=lat, lon=lon,
        shore_power=False, shore_v=0.0, shore_a=0.0,
        power_source="battery",
        anchor_armed=True,
        anchor_distance_m=distance_m,
        wind_apparent_kt=jittered(15.0, 3, rng=rng),
        wind_true_kt=jittered(16.0, 3, rng=rng),
    )


def _underway(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    base = _normal(t, prev, rng)
    lat, lon = ((SLIP_LAT, SLIP_LON) if t < 1
                else gps_track(prev.lat, prev.lon, 5.2, 45.0, dt_s=1.0))
    targets, nname, nrange = _build_ais(rng, 8)
    return replace(
        base,
        shore_power=False, shore_v=0.0, shore_a=0.0,
        generator=False, gen_v=0.0,
        power_source="battery",
        house_v=jittered(linear_ramp(t, 0, 14400, 12.6, 12.0), 0.04, rng=rng),
        house_a=jittered(-4.5, 0.5, rng=rng),
        house_soc=jittered(linear_ramp(t, 0, 14400, 85, 60), 0.6, rng=rng),
        engine_running=True,
        engine_rpm=int(jittered(2200, 50, rng=rng)),
        engine_oil_pressure_kpa=jittered(380, 10, rng=rng),
        engine_coolant_c=jittered(82, 1, rng=rng),
        engine_alt_v=jittered(14.1, 0.1, rng=rng),
        engine_runtime_h=base.engine_runtime_h + t / 3600,
        lat=lat, lon=lon,
        sog_kt=jittered(5.2, 0.4, rng=rng),
        cog_deg=jittered(45.0, 3.0, rng=rng),
        heading_deg=jittered(48.0, 4.0, rng=rng),
        depth_m=jittered(14.5, 1.5, rng=rng),
        speed_through_water_kt=jittered(5.0, 0.4, rng=rng),
        wind_apparent_kt=jittered(12.0, 2, rng=rng),
        wind_apparent_deg=jittered(40, 8, rng=rng),
        wind_true_kt=jittered(14.0, 2, rng=rng),
        wind_true_deg=jittered(80, 10, rng=rng),
        heel_deg=jittered(8.0, 2, rng=rng),
        pitch_deg=jittered(2.0, 1, rng=rng),
        ais_targets_in_range=len(targets),
        ais_nearest_name=nname,
        ais_nearest_range_nm=nrange,
        ais_targets=targets,
    )


def _all_critical(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    base = _normal(t, prev, rng)
    targets, nname, nrange = _build_ais(rng, 6)
    return replace(
        base,
        shore_power=False, shore_v=0.0, shore_a=0.0,
        generator=False, gen_v=0.0,
        power_source="battery",
        house_v=jittered(11.4, 0.03, rng=rng),
        house_a=jittered(-9.0, 0.5, rng=rng),
        house_soc=jittered(18, 0.6, rng=rng),
        house_ttg_min=int(jittered(45, 10, rng=rng)),
        start_v=jittered(11.9, 0.05, rng=rng),
        bilge_wet=True,
        bilge_pump_cycles_today=22,
        cabin_temp_c=jittered(35.0, 0.5, rng=rng),
        engine_temp_c=jittered(60.0, 1.0, rng=rng),
        engine_air_temp_c=jittered(70.0, 1.0, rng=rng),
        fridge_temp_c=jittered(12.0, 0.3, rng=rng),
        freezer_temp_c=jittered(-2.0, 0.3, rng=rng),
        cabin_humidity_pct=jittered(85, 2, rng=rng),
        cabin_pressure_hpa=jittered(998, 0.5, rng=rng),
        co_ppm=jittered(45, 5, rng=rng),
        smoke_alarm=True,
        leak_head=True, leak_engine=True,
        depth_m=jittered(2.4, 0.2, rng=rng),  # shallow!
        wind_apparent_kt=jittered(28, 3, rng=rng),
        wind_true_kt=jittered(30, 3, rng=rng),
        heel_deg=jittered(22, 4, rng=rng),
        anchor_armed=True,
        anchor_distance_m=jittered(72, 5, rng=rng),
        slip_distance_m=jittered(1500, 10, rng=rng),
        forepeak_hatch_open=True,
        rssi_dbm=int(jittered(-85, 3, rng=rng)),
        uptime_s=int(t),
        sog_kt=jittered(0.8, 0.2, rng=rng),
        cog_deg=jittered(180.0, 30.0, rng=rng),
        ais_targets_in_range=len(targets),
        ais_nearest_name=nname,
        ais_nearest_range_nm=nrange,
        ais_targets=targets,
    )


# ─── cycle ────────────────────────────────────────────────────────────
_CYCLE_ORDER = ["normal", "low_battery", "shore_lost", "gen_running",
                "anchor_drag", "underway", "bilge_wet", "all_critical"]
_CYCLE_DURATION_S = 90.0


def _cycle(t: float, prev: SensorSnapshot, rng: random.Random) -> SensorSnapshot:
    idx = int(t // _CYCLE_DURATION_S) % len(_CYCLE_ORDER)
    sub_name = _CYCLE_ORDER[idx]
    sub_t = t % _CYCLE_DURATION_S
    return SCENARIOS[sub_name](sub_t, prev, rng)


SCENARIOS: dict[str, ScenarioFn] = {
    "normal": _normal,
    "low_battery": _low_battery,
    "bilge_wet": _bilge_wet,
    "shore_lost": _shore_lost,
    "gen_running": _gen_running,
    "anchor_drag": _anchor_drag,
    "underway": _underway,
    "all_critical": _all_critical,
    "cycle": _cycle,
}

DEFAULT_SCENARIO = "normal"


def list_scenarios() -> Iterable[str]:
    return SCENARIOS.keys()


def get_scenario(name: str) -> ScenarioFn:
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario {name!r}.")
    return SCENARIOS[name]
