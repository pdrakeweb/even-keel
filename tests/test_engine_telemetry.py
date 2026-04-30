"""Binds tests/features/telemetry/engine_telemetry.feature to pytest.

Step modules are imported via conftest.py.
"""
from __future__ import annotations

from pytest_bdd import scenarios

scenarios("features/telemetry/engine_telemetry.feature")
