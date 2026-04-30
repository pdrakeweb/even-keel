"""Binds tests/features/alerts/anchor_alarm.feature to pytest.

Skipped at module level if HA env vars aren't set, same as the bilge
and battery alarm scenarios.
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

scenarios("features/alerts/anchor_alarm.feature")
