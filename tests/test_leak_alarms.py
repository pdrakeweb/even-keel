"""Binds tests/features/telemetry/leak_alarms.feature to pytest.

Step modules are imported via conftest.py.
"""
from __future__ import annotations

from pytest_bdd import scenarios

scenarios("features/telemetry/leak_alarms.feature")
