"""Binds tests/features/alerts/bilge_alarm_minimal.feature to pytest.

Step modules are imported via conftest.py.

Skipped wholesale if HA_URL/HA_TOKEN env vars aren't set — local dev
without HA stays green; CI runs them against the integration-tests
workflow's HA service container.
"""
from __future__ import annotations

import os

import pytest
from pytest_bdd import scenarios

if not os.environ.get("HA_URL") or not os.environ.get("HA_TOKEN"):
    pytest.skip(
        "HA_URL + HA_TOKEN not configured; skipping HA-entity scenarios",
        allow_module_level=True,
    )

scenarios("features/alerts/bilge_alarm_minimal.feature")
