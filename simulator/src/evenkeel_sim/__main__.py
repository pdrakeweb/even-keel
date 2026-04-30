"""Entry point: ``python -m evenkeel_sim``."""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from .publisher import SimulatorPublisher
from .scenarios import DEFAULT_SCENARIO, list_scenarios


def main() -> None:
    parser = argparse.ArgumentParser(prog="evenkeel-sim", description=__doc__)
    parser.add_argument("--broker", default=os.environ.get("MQTT_BROKER", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", "1883")))
    parser.add_argument("--username", default=os.environ.get("MQTT_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("MQTT_PASSWORD"))
    parser.add_argument(
        "--scenario",
        default=os.environ.get("INITIAL_SCENARIO", DEFAULT_SCENARIO),
        choices=list(list_scenarios()),
    )
    parser.add_argument(
        "--start-paused",
        action="store_true",
        default=os.environ.get("START_PAUSED", "").lower() in {"1", "true", "yes"},
        help="Start with running=false (waits for HA to flip the toggle)",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    publisher = SimulatorPublisher(
        broker=args.broker,
        port=args.port,
        username=args.username,
        password=args.password,
        initial_scenario=args.scenario,
        run_initially=not args.start_paused,
    )
    try:
        asyncio.run(publisher.run())
    except KeyboardInterrupt:
        logging.getLogger("evenkeel_sim").info("Bye.")
        sys.exit(0)


if __name__ == "__main__":
    main()
