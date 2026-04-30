"""Binds tests/features/telemetry/battery_telemetry.feature to pytest.

Step definitions are loaded via conftest.py imports — see
`from steps.battery_steps import *` there. This module just needs to
declare the scenario binding so pytest-bdd discovers the feature file.
"""
from __future__ import annotations

from pytest_bdd import scenarios

scenarios("features/telemetry/battery_telemetry.feature")
