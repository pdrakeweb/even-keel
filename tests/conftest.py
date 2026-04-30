"""pytest configuration and adapter-selection fixture.

`--mode=virtual|hil|live` picks the BoatAdapter implementation. Step definitions
call the `boat` fixture — they never reference the adapter directly.

Step modules are imported eagerly here so pytest-bdd discovers them
as fixtures available to every test in this directory tree.
"""
from __future__ import annotations

import asyncio
import sys

import pytest

# aiomqtt uses asyncio.add_writer/remove_writer, which the Windows
# ProactorEventLoop doesn't implement. Force the SelectorEventLoop on
# Windows so local dev mirrors CI (which runs on Linux). Set this BEFORE
# any aiomqtt-importing module loads.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# pytest-bdd 8 registers step definitions in a global registry when the
# decorator runs. Importing the step modules at conftest scope ensures
# every @given/@when/@then is registered before any scenario executes,
# regardless of which test_*.py module discovers the .feature file.
from steps.battery_steps import *  # noqa: F401, F403
from steps.bilge_steps import *  # noqa: F401, F403
from steps.common_steps import *  # noqa: F401, F403


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
