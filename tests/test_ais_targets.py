"""Binds tests/features/ais/ais_targets.feature to pytest.

Step modules are imported via conftest.py.
"""
from __future__ import annotations

from pytest_bdd import scenarios

scenarios("features/ais/ais_targets.feature")
