"""Tests for the math helpers used by scenarios.

These are pure functions — perfect TDD targets.
"""
from __future__ import annotations

import math
import random

import pytest

from evenkeel_sim.generators import (
    Transient,
    fridge_cycle,
    gps_drift_around,
    gps_track,
    jittered,
    linear_ramp,
    random_walk,
    slow_drift,
)


class TestJittered:
    def test_jitter_zero_returns_base_exactly(self, rng):
        assert jittered(10.0, 0.0, rng=rng) == 10.0

    def test_jitter_within_envelope(self, rng):
        for _ in range(200):
            v = jittered(50.0, 1.5, rng=rng)
            assert 48.5 <= v <= 51.5

    def test_jitter_distribution_centers_near_base(self, rng):
        samples = [jittered(0.0, 1.0, rng=rng) for _ in range(2000)]
        mean = sum(samples) / len(samples)
        assert abs(mean) < 0.1, f"Mean drift {mean} should be near 0"


class TestSlowDrift:
    def test_period_zero_handled(self):
        # Defensive — this should at least not crash. Documented behavior:
        # period_s == 0 raises ZeroDivisionError; callers must guard.
        with pytest.raises(ZeroDivisionError):
            slow_drift(10.0, 0, 1.0, 5.0)

    def test_amplitude_zero_returns_base(self):
        assert slow_drift(10.0, 60.0, 0.0, 5.0) == 10.0

    def test_period_quarter_returns_amplitude_max(self):
        # sin(2π * 0.25) = sin(π/2) = 1
        assert math.isclose(slow_drift(0.0, 100.0, 1.0, 25.0), 1.0)

    def test_period_full_returns_base(self):
        # sin(2π) = 0
        assert math.isclose(slow_drift(10.0, 100.0, 5.0, 100.0), 10.0, abs_tol=1e-9)


class TestRandomWalk:
    def test_walk_clamped_to_bounds(self, rng):
        v = 5.0
        for _ in range(500):
            v = random_walk(v, step=10.0, lo=0.0, hi=10.0, rng=rng)
            assert 0.0 <= v <= 10.0

    def test_walk_with_zero_step_returns_prev(self, rng):
        assert random_walk(7.0, step=0.0, lo=0.0, hi=10.0, rng=rng) == 7.0


class TestFridgeCycle:
    def test_cycle_stays_within_band(self):
        for t in range(0, 3600, 30):
            v = fridge_cycle(t)
            assert 1.5 <= v <= 7.0, f"Fridge cycle out of band at t={t}: {v}"

    def test_cycle_is_periodic(self):
        # Default period is 1800s
        v0 = fridge_cycle(0.0)
        v_next_period = fridge_cycle(1800.0)
        assert math.isclose(v0, v_next_period, abs_tol=0.01)

    def test_cycle_cooling_phase_decreases(self):
        # Phase 0..30% is cooling: high → low
        v_start = fridge_cycle(0.0)
        v_end_cool = fridge_cycle(540.0)  # 0.3 * 1800
        assert v_end_cool < v_start


class TestLinearRamp:
    def test_before_start_returns_v_start(self):
        assert linear_ramp(t_now=5, t_start=10, t_end=20, v_start=0, v_end=10) == 0

    def test_after_end_returns_v_end(self):
        assert linear_ramp(t_now=25, t_start=10, t_end=20, v_start=0, v_end=10) == 10

    def test_midpoint_returns_average(self):
        assert linear_ramp(t_now=15, t_start=10, t_end=20, v_start=0, v_end=10) == 5.0

    def test_negative_ramp_works(self):
        assert linear_ramp(t_now=15, t_start=10, t_end=20, v_start=12.6, v_end=11.0) == pytest.approx(11.8)


class TestTransient:
    def test_inside_window(self):
        t = Transient(start_s=10, end_s=20)
        assert not t.active(5)
        assert t.active(10)
        assert t.active(15)
        assert not t.active(20)  # end is exclusive
        assert not t.active(25)

    def test_zero_width_window_never_active(self):
        t = Transient(start_s=10, end_s=10)
        for s in range(0, 30):
            assert not t.active(s)


class TestGpsDriftAround:
    def test_zero_radius_returns_center(self, rng):
        lat, lon = gps_drift_around(41.4536, -82.7100, radius_m=0.0, t=0, rng=rng)
        assert lat == 41.4536
        assert lon == -82.7100

    def test_drift_stays_near_center(self, rng):
        center_lat, center_lon = 41.4536, -82.7100
        for _ in range(50):
            lat, lon = gps_drift_around(center_lat, center_lon, radius_m=10.0, t=0, rng=rng)
            # ~10m radius => ~0.0001 degree variance — allow 3x for gaussian tail
            assert abs(lat - center_lat) < 0.001
            assert abs(lon - center_lon) < 0.001


class TestGpsTrack:
    def test_zero_speed_returns_origin(self):
        lat, lon = gps_track(41.0, -82.0, sog_kt=0.0, cog_deg=45.0, dt_s=10.0)
        assert lat == 41.0
        assert lon == -82.0

    def test_due_north_increases_lat_only(self):
        lat0, lon0 = 41.0, -82.0
        lat, lon = gps_track(lat0, lon0, sog_kt=10.0, cog_deg=0.0, dt_s=60.0)
        assert lat > lat0
        assert math.isclose(lon, lon0, abs_tol=1e-6)

    def test_due_east_increases_lon_only(self):
        lat0, lon0 = 41.0, -82.0
        lat, lon = gps_track(lat0, lon0, sog_kt=10.0, cog_deg=90.0, dt_s=60.0)
        assert math.isclose(lat, lat0, abs_tol=1e-6)
        assert lon > lon0

    def test_distance_at_one_knot_for_one_hour_is_about_one_nm(self):
        # 1 nm = 1852 m. 1 kt = 1 nm/h. After 3600s at 0° heading,
        # latitude increases by roughly 1852/111111 ≈ 0.01667°
        lat0 = 0.0
        lat, _ = gps_track(lat0, 0.0, sog_kt=1.0, cog_deg=0.0, dt_s=3600.0)
        assert math.isclose(lat - lat0, 1852.0 / 111_111, rel_tol=0.01)
