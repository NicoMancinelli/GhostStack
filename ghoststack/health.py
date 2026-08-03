"""Hardware health diagnostics."""

import logging
import os
import subprocess
from typing import Dict, Optional

try:
    import serial
except ImportError:
    serial = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [HEALTH] - %(message)s")


def check_sdr() -> str:
    try:
        res = subprocess.run(
            ["hackrf_info"], capture_output=True, text=True, timeout=2
        )
        if res.returncode == 0:
            return "HackRF One Detected"
        res = subprocess.run(
            ["rtl_test", "-t"], capture_output=True, text=True, timeout=2
        )
        if "No supported devices found" not in (res.stderr or ""):
            return "RTL-SDR Detected"
    except Exception:
        pass
    return "SDR NOT FOUND"


def check_serial(port: Optional[str]) -> str:
    if not port:
        return "Not Configured"
    if serial is None:
        return "pyserial unavailable"
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        ser.close()
        return f"ESP32 Connected on {port}"
    except Exception:
        return f"PORT {port} OFFLINE"


def get_system_load() -> str:
    try:
        load = os.getloadavg()
        return f"Load: {load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f}"
    except Exception:
        return "Unknown"


def run_full_diagnostic(esp_port: Optional[str] = None) -> Dict[str, str]:
    return {
        "sdr": check_sdr(),
        "esp32": check_serial(esp_port),
        "system": get_system_load(),
    }
