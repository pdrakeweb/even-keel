"""BoatAdapter implementations.

Step definitions in tests/steps/ never know which adapter is wired in;
they call methods on the abstract BoatAdapter Protocol. The concrete
implementation is selected at the conftest level via --mode.

Concrete adapters are imported lazily by conftest.py to avoid pulling
in mode-specific deps (pyserial, etc.) when they aren't being used.
"""
from .base import BoatAdapter

__all__ = ["BoatAdapter"]
