"""Shared pytest fixtures for simulator tests.

Most tests use a deterministic `random.Random(seed)` fixture so jitter
and AIS target picks are reproducible — important for invariant tests
that need to be stable across runs.
"""
from __future__ import annotations

import random

import pytest


@pytest.fixture
def rng() -> random.Random:
    """Deterministic RNG so scenario outputs are reproducible."""
    return random.Random(0xEEC7E)  # "EVE C[7]" — eyebrow-friendly seed
