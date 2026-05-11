#!/bin/bash

# GhostStack Dependency Installation Script
# Target: Kali Linux (Debian-based)

set -e

echo "[*] GhostStack: Starting dependency installation..."

# Update Package Lists
sudo apt update

# Install Core RF/EW Tools
echo "[*] Installing RF/EW Layer..."
sudo apt install -y \
    gnuradio \
    rtl-sdr \
    hackrf \
    gqrx-sdr \
    inspectrum \
    libitpp-dev

# Install Network Layer Tools
echo "[*] Installing Network Layer..."
sudo apt install -y \
    aircrack-ng \
    wireshark \
    tshark \
    python3-scapy \
    python3-pip

# Install ROS 2 Base (Humble) - Note: Adjust for specific Kali versions
# This follows the standard Debian-based installation approach
echo "[*] Installing ROS 2 Base Libraries..."
sudo apt install -y \
    ros-base-dev \
    python3-colcon-common-extensions \
    python3-rosdep

# Install Python Requirements
echo "[*] Installing Python dependencies..."
pip3 install -r requirements.txt --break-system-packages || pip3 install -r requirements.txt

# Post-Install Setup
sudo rosdep init || echo "[!] rosdep already initialized"
rosdep update

echo "[+] Installation Complete. Please reboot to ensure all SDR rules are applied."
