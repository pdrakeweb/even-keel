"""Helpers for generating realistic sensor noise, drift, and transient events."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable


def jittered(base: float, jitter: float, *, rng: random.Random | None = None) -> float:
    """Return base + uniform jitter in ±jitter."""
    r = rng if rng is not None else random
    return base + r.uniform(-jitter, jitter)


def slow_drift(base: float, period_s: float, amplitude: float, t: float) -> float:
    """Gentle sine-wave drift (for things like cabin temp over the day)."""
    return base + amplitude * math.sin(2 * math.pi * t / period_s)


def random_walk(prev: float, step: float, lo: float, hi: float,
                rng: random.Random | None = None) -> float:
    """Bounded random-walk update."""
    r = rng if rng is not None else random
    new = prev + r.gauss(0, step)
    return max(lo, min(hi, new))


def fridge_cycle(t: float, low: float = 2.0, high: float = 6.5,
                 period_s: float = 1800.0) -> float:
    """Sawtooth modeling fridge thermostat cycling."""
    phase = (t % period_s) / period_s
    if phase < 0.3:
        return high - (high - low) * (phase / 0.3)  # cooling
    return low + (high - low) * ((phase - 0.3) / 0.7)  # warming


def linear_ramp(t_now: float, t_start: float, t_end: float,
                v_start: float, v_end: float) -> float:
    """Clamp-aware linear ramp from v_start@t_start to v_end@t_end."""
    if t_now <= t_start:
        return v_start
    if t_now >= t_end:
        return v_end
    f = (t_now - t_start) / (t_end - t_start)
    return v_start + (v_end - v_start) * f


@dataclass
class Transient:
    """A bool that goes True for a window inside a scenario."""
    start_s: float
    end_s: float

    def active(self, t_in_scenario_s: float) -> bool:
        return self.start_s <= t_in_scenario_s < self.end_s


def gps_drift_around(center_lat: float, center_lon: float,
                     radius_m: float, t: float,
                     rng: random.Random | None = None) -> tuple[float, float]:
    """Return (lat, lon) that drift inside a circle of given radius."""
    r = rng if rng is not None else random
    # 1 degree latitude ≈ 111_111 m
    bearing = r.uniform(0, 2 * math.pi)
    distance_m = abs(r.gauss(0, radius_m / 3))
    dlat = (distance_m * math.cos(bearing)) / 111_111
    dlon = (distance_m * math.sin(bearing)) / (111_111 * math.cos(math.radians(center_lat)))
    return center_lat + dlat, center_lon + dlon


def gps_track(lat0: float, lon0: float, sog_kt: float, cog_deg: float,
              dt_s: float) -> tuple[float, float]:
    """Move (lat, lon) by sog_kt knots on cog_deg bearing for dt_s seconds."""
    if sog_kt <= 0:
        return lat0, lon0
    distance_m = sog_kt * 0.514444 * dt_s  # 1 kt = 0.514444 m/s
    bearing = math.radians(cog_deg)
    dlat = (distance_m * math.cos(bearing)) / 111_111
    dlon = (distance_m * math.sin(bearing)) / (111_111 * math.cos(math.radians(lat0)))
    return lat0 + dlat, lon0 + dlon
