"""pytest configuration and adapter-selection fixture.

`--mode=virtual|hil|live` picks the BoatAdapter implementation. Step definitions
call the `boat` fixture — they never reference the adapter directly.
"""
from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--mode",
        action="store",
        default="virtual",
        choices=["virtual", "hil", "live"],
        help="test harness mode",
    )
    parser.addoption(
        "--hil-port",
        action="store",
        default="/dev/ttyUSB0",
        help="serial port of the HIL stimulator ESP32 (hil mode only)",
    )
    parser.addoption(
        "--broker",
        action="store",
        default="localhost",
        help="MQTT broker host (live mode only — deployed firmware target)",
    )


@pytest.fixture(scope="session")
async def boat(request: pytest.FixtureRequest):
    mode = request.config.getoption("--mode")
    if mode == "virtual":
        from adapters.virtual import VirtualAdapter
        adapter = VirtualAdapter()
    elif mode == "hil":
        from adapters.hil import HilAdapter
        adapter = HilAdapter(port=request.config.getoption("--hil-port"))
    elif mode == "live":
        from adapters.live import LiveIntegrationAdapter
        adapter = LiveIntegrationAdapter(
            broker=request.config.getoption("--broker")
        )
    else:
        raise ValueError(f"unknown mode: {mode}")

    await adapter.startup()
    try:
        yield adapter
    finally:
        await adapter.shutdown()
