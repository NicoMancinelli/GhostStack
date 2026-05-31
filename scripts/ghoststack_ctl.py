#!/usr/bin/env python3
"""GhostStack CLI — thin entrypoint over the modular core library."""

import argparse
import sys

from ghoststack.health import run_full_diagnostic
from ghoststack.modules import profile_for
from ghoststack.pidfile import stop_supervisor
from ghoststack.supervisor import GhostStackSupervisor


def main():
    parser = argparse.ArgumentParser(description="GhostStack Supervisor")
    parser.add_argument(
        "command",
        choices=["start-all", "start-rf", "start-network", "stop-all", "diagnose"],
    )
    parser.add_argument("--esp-port", default="/dev/ttyUSB0")
    parser.add_argument(
        "--sentry",
        action="store_true",
        help="Enable active sentry profile (extra modules, lower RF thresholds)",
    )
    args = parser.parse_args()

    if args.command == "stop-all":
        stop_supervisor()
        return

    if args.command == "diagnose":
        run_full_diagnostic(args.esp_port)
        return

    modules = profile_for(args.command, sentry=args.sentry)
    if not modules:
        print(f"[-] Unknown profile for command: {args.command}")
        sys.exit(1)

    GhostStackSupervisor(
        modules,
        esp_port=args.esp_port,
        sentry_mode=args.sentry,
    ).run()


if __name__ == "__main__":
    main()
