"""Binds tests/features/telemetry/bilge_publication.feature to pytest.

pytest-bdd discovers a feature file only when a test_*.py module
references it via `@scenarios()` or `@scenario()`. We use scenarios()
to bind every scenario in the file at once. Step definitions are
imported eagerly so pytest-bdd can resolve them during collection.
"""
from __future__ import annotations

from pytest_bdd import scenarios

# Eager imports register step definitions with pytest-bdd:
from steps import bilge_steps  # noqa: F401
from steps import common_steps  # noqa: F401

scenarios("features/telemetry/bilge_publication.feature")
