"""Scenario invariant tests.

Each scenario must:
- produce a SensorSnapshot with correct types for every primitive field
- never return None for non-Optional fields
- satisfy scenario-specific invariants (e.g., bilge_wet scenario actually
  flips bilge_wet to True at some point during the wet window)
- be reproducible given a seeded RNG
"""
from __future__ import annotations

from dataclasses import fields
import math

import pytest

from evenkeel_sim.scenarios import (
    SCENARIOS,
    DEFAULT_SCENARIO,
    SLIP_LAT,
    SLIP_LON,
    get_scenario,
    list_scenarios,
)
from evenkeel_sim.sensors import SensorSnapshot


ALL_NAMES = sorted(list_scenarios())


class TestRegistry:
    def test_default_scenario_is_in_registry(self):
        assert DEFAULT_SCENARIO in SCENARIOS

    def test_get_scenario_unknown_raises(self):
        with pytest.raises(ValueError):
            get_scenario("not-a-real-scenario")

    def test_expected_scenarios_present(self):
        expected = {
            "normal", "low_battery", "bilge_wet", "shore_lost",
            "gen_running", "anchor_drag", "underway", "all_critical",
            "cycle",
        }
        assert expected.issubset(set(ALL_NAMES))


class TestSnapshotShape:
    """Every scenario must produce a structurally-valid SensorSnapshot."""

    @pytest.mark.parametrize("scenario_name", ALL_NAMES)
    def test_returns_sensor_snapshot(self, scenario_name, rng):
        fn = get_scenario(scenario_name)
        snap = fn(0.0, SensorSnapshot(), rng)
        assert isinstance(snap, SensorSnapshot)

    @pytest.mark.parametrize("scenario_name", ALL_NAMES)
    def test_no_unexpected_none_fields(self, scenario_name, rng):
        # house_soc is the only legitimately-Optional primitive (None pre-Phase 7).
        # Every other field must be set.
        fn = get_scenario(scenario_name)
        snap = fn(0.0, SensorSnapshot(), rng)
        for f in fields(snap):
            if f.name == "house_soc":
                continue
            value = getattr(snap, f.name)
            assert value is not None, f"{scenario_name}: field {f.name} is None"

    @pytest.mark.parametrize("scenario_name", ALL_NAMES)
    def test_voltages_in_plausible_range(self, scenario_name, rng):
        fn = get_scenario(scenario_name)
        snap = fn(0.0, SensorSnapshot(), rng)
        # Lead-acid lower bound 9V is dead, upper bound 15V is overcharged.
        # Scenarios should always be in an electrically-sensible band.
        assert 9.0 <= snap.house_v <= 15.0
        assert 9.0 <= snap.start_v <= 15.0

    @pytest.mark.parametrize("scenario_name", ALL_NAMES)
    def test_position_is_finite_and_in_lake_erie_bounds(self, scenario_name, rng):
        # We don't ship Hunter 41DS to the open ocean in any scenario.
        fn = get_scenario(scenario_name)
        snap = fn(0.0, SensorSnapshot(), rng)
        assert math.isfinite(snap.lat)
        assert math.isfinite(snap.lon)
        # Lake Erie roughly: 41.3-42.7°N, -83.5 to -78.8°W
        assert 41.0 < snap.lat < 43.0
        assert -84.0 < snap.lon < -78.0

    @pytest.mark.parametrize("scenario_name", ALL_NAMES)
    def test_temperatures_finite(self, scenario_name, rng):
        fn = get_scenario(scenario_name)
        snap = fn(0.0, SensorSnapshot(), rng)
        for f in [
            "cabin_temp_c", "engine_temp_c", "fridge_temp_c",
            "freezer_temp_c", "engine_air_temp_c", "lazarette_temp_c",
        ]:
            v = getattr(snap, f)
            assert math.isfinite(v), f"{scenario_name}: {f} non-finite ({v})"


class TestNormalScenario:
    """The 'normal' scenario describes a healthy boat at the slip."""

    def test_normal_boat_is_at_slip(self, rng):
        snap = get_scenario("normal")(0.0, SensorSnapshot(), rng)
        assert math.isclose(snap.lat, SLIP_LAT, abs_tol=0.01)
        assert math.isclose(snap.lon, SLIP_LON, abs_tol=0.01)

    def test_normal_boat_has_shore_power(self, rng):
        snap = get_scenario("normal")(0.0, SensorSnapshot(), rng)
        assert snap.shore_power is True
        assert snap.power_source == "shore"
        assert snap.generator is False

    def test_normal_boat_no_alarms(self, rng):
        snap = get_scenario("normal")(0.0, SensorSnapshot(), rng)
        assert snap.bilge_wet is False
        assert snap.smoke_alarm is False
        assert snap.leak_head is False
        assert snap.leak_galley is False
        assert snap.leak_engine is False

    def test_normal_house_battery_healthy(self, rng):
        snap = get_scenario("normal")(0.0, SensorSnapshot(), rng)
        assert snap.house_v >= 12.4

    def test_normal_engine_off(self, rng):
        snap = get_scenario("normal")(0.0, SensorSnapshot(), rng)
        assert snap.engine_running is False
        assert snap.engine_rpm == 0


class TestBilgeWetScenario:
    def test_bilge_wet_during_window(self, rng):
        # The implementation puts wet between t=30 and t=120.
        fn = get_scenario("bilge_wet")
        wet_at_60 = fn(60.0, SensorSnapshot(), rng).bilge_wet
        assert wet_at_60 is True

    def test_bilge_dry_outside_window(self, rng):
        fn = get_scenario("bilge_wet")
        assert fn(0.0, SensorSnapshot(), rng).bilge_wet is False
        assert fn(150.0, SensorSnapshot(), rng).bilge_wet is False


class TestLowBatteryScenario:
    def test_battery_sags_over_time(self, rng):
        # Linear ramp 12.6 -> 11.7 over 0..600s. By t=300 we're halfway:
        # ≈ 12.15. With +/-0.04 jitter we should be below 12.3.
        fn = get_scenario("low_battery")
        midway = fn(300.0, SensorSnapshot(), rng).house_v
        assert midway < 12.3

    def test_battery_critical_during_sag(self, rng):
        fn = get_scenario("low_battery")
        # By t=600 the ramp reaches 11.7V
        sagging = fn(580.0, SensorSnapshot(), rng).house_v
        assert sagging < 11.85

    def test_generator_runs_after_sag(self, rng):
        fn = get_scenario("low_battery")
        snap = fn(700.0, SensorSnapshot(), rng)
        # In the 600..1800 window the generator is running.
        assert snap.generator is True
        assert snap.power_source == "generator"


class TestShoreLostScenario:
    def test_after_disconnect_shore_off(self, rng):
        fn = get_scenario("shore_lost")
        # Disconnect happens at t=15
        snap = fn(60.0, SensorSnapshot(), rng)
        assert snap.shore_power is False
        assert snap.power_source == "battery"


class TestUnderwayScenario:
    def test_underway_engine_running(self, rng):
        snap = get_scenario("underway")(120.0, SensorSnapshot(lat=SLIP_LAT, lon=SLIP_LON), rng)
        assert snap.engine_running is True
        assert snap.engine_rpm > 1500

    def test_underway_position_moves_over_time(self, rng):
        fn = get_scenario("underway")
        # First call seeds prev to a known starting spot
        snap0 = fn(1.0, SensorSnapshot(lat=SLIP_LAT, lon=SLIP_LON), rng)
        snap1 = fn(2.0, snap0, rng)
        # The boat should have moved (5+ kt over 1s ≈ 2-3m, tiny but nonzero)
        assert (snap0.lat, snap0.lon) != (snap1.lat, snap1.lon)


class TestAnchorDragScenario:
    def test_drag_distance_grows_after_60s(self, rng):
        # gps_drift_around uses gauss(0, radius/3) for the magnitude, so a
        # single sample is rarely close to `radius`. Use mean over many
        # samples to verify the trend.
        fn = get_scenario("anchor_drag")
        early_samples = [fn(30.0, SensorSnapshot(), rng).anchor_distance_m for _ in range(50)]
        late_samples = [fn(180.0, SensorSnapshot(), rng).anchor_distance_m for _ in range(50)]
        early_mean = sum(early_samples) / len(early_samples)
        late_mean = sum(late_samples) / len(late_samples)
        assert late_mean > early_mean
        # By t=180, radius is 8 + 120*0.8 = 104m. Mean magnitude of
        # gauss(0, 104/3) ~ 27m. That's "dragging".
        assert late_mean > 15

    def test_drag_arms_anchor(self, rng):
        snap = get_scenario("anchor_drag")(0.0, SensorSnapshot(), rng)
        assert snap.anchor_armed is True


class TestAllCriticalScenario:
    def test_all_critical_flips_every_alarm(self, rng):
        snap = get_scenario("all_critical")(0.0, SensorSnapshot(), rng)
        assert snap.bilge_wet is True
        assert snap.smoke_alarm is True
        assert snap.leak_head is True or snap.leak_engine is True
        assert snap.house_v < 12.0
        assert snap.anchor_armed is True


class TestCycle:
    def test_cycle_rotates_through_subscenarios(self, rng):
        fn = get_scenario("cycle")
        # Cycle period = 90s per sub-scenario, 8 sub-scenarios
        # t=0 -> first sub-scenario
        # t=90 -> second
        # etc.
        s_first = fn(10.0, SensorSnapshot(), rng)
        s_second = fn(100.0, SensorSnapshot(), rng)
        # The two snapshots should differ in at least one observable field
        # (different sub-scenarios have different shore_power / engine_running etc).
        differences = sum(
            1 for f in fields(s_first)
            if getattr(s_first, f.name) != getattr(s_second, f.name)
        )
        assert differences > 0

    def test_cycle_returns_to_first_after_full_period(self, rng):
        # Full period = 8 sub-scenarios * 90s = 720s
        fn = get_scenario("cycle")
        s_first = fn(0.5, SensorSnapshot(), rng)
        s_after_period = fn(720.5, SensorSnapshot(), rng)
        # Both should be in the same sub-scenario ('normal')
        assert s_first.shore_power == s_after_period.shore_power
        assert s_first.engine_running == s_after_period.engine_running
