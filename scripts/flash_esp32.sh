#!/bin/bash
# GhostStack: Automated ESP32 Flasher
#
# Compiles and uploads the Optical Strobe firmware using arduino-cli.
# Ensure your ESP32 is connected via USB.

set -e

PORT=${1:-/dev/ttyUSB0}
SKETCH="optical_disruption/esp32/optical_strobe/optical_strobe.ino"
FQBN="esp32:esp32:esp32s3"

echo "[*] GhostStack Hardware Flasher"
echo "[*] Target FQBN: $FQBN"
echo "[*] Target Port: $PORT"
echo "-----------------------------------"

if ! command -v arduino-cli &> /dev/null; then
    echo "[-] arduino-cli could not be found."
    echo "[!] Please install it: curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh"
    exit 1
fi

echo "[*] Compiling firmware..."
arduino-cli compile --fqbn $FQBN $SKETCH

echo "[*] Uploading firmware..."
arduino-cli upload -p $PORT --fqbn $FQBN $SKETCH

echo "[+] Optical Module successfully flashed!"
