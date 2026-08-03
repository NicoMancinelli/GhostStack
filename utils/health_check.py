"""Backward-compatible health check shim — prefer ghoststack.health."""

from ghoststack.health import check_sdr, check_serial, get_system_load, run_full_diagnostic

__all__ = ["check_sdr", "check_serial", "get_system_load", "run_full_diagnostic"]

if __name__ == "__main__":
    run_full_diagnostic("/dev/ttyUSB0")
