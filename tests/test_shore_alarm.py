"""Binds tests/features/alerts/shore_alarm.feature to pytest.

Skipped at module level if HA env vars aren't set; runs only against
the CI HA service container.
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

scenarios("features/alerts/shore_alarm.feature")
