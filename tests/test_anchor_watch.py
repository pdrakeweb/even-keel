"""Binds tests/features/telemetry/anchor_watch.feature to pytest.

Step modules are imported via conftest.py.
"""
from __future__ import annotations

from pytest_bdd import scenarios

scenarios("features/telemetry/anchor_watch.feature")
