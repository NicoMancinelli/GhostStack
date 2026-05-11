import subprocess
import serial
import os
import logging

# GhostStack: Hardware Health Monitor
# Checks for the presence and responsiveness of critical hardware.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [HEALTH] - %(message)s')

def check_sdr():
    """Checks for HackRF or RTL-SDR via shell commands."""
    try:
        # Check for HackRF
        res = subprocess.run(['hackrf_info'], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            return "HackRF One Detected"
        
        # Check for RTL-SDR
        res = subprocess.run(['rtl_test', '-t'], capture_output=True, text=True, timeout=2)
        if "No supported devices found" not in res.stderr:
            return "RTL-SDR Detected"
            
    except Exception:
        pass
    return "SDR NOT FOUND"

def check_serial(port):
    """Checks if the ESP32 Serial port is accessible."""
    if not port:
        return "Not Configured"
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        ser.close()
        return f"ESP32 Connected on {port}"
    except Exception:
        return f"PORT {port} OFFLINE"

def get_system_load():
    """Returns basic RPi5 system load info."""
    try:
        load = os.getloadavg()
        return f"Load: {load[0]}, {load[1]}, {load[2]}"
    except Exception:
        return "Unknown"

def run_full_diagnostic(esp_port=None):
    results = {
        "sdr": check_sdr(),
        "esp32": check_serial(esp_port),
        "system": get_system_load()
    }
    for k, v in results.items():
        logging.info(f"{k.upper()}: {v}")
    return results

if __name__ == "__main__":
    run_full_diagnostic("/dev/ttyUSB0")
