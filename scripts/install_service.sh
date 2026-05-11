#!/bin/bash
# GhostStack: systemd Service Installer
# Installs GhostStack to run as a persistent background daemon.

set -e

echo "[*] Installing GhostStack systemd service..."

# Assume repo is cloned to /opt/GhostStack for production deployment
if [ "$PWD" != "/opt/GhostStack" ]; then
    echo "[!] For production, GhostStack should ideally be in /opt/GhostStack."
    echo "[!] Updating service file with current directory: $PWD"
    sed -i "s|WorkingDirectory=/opt/GhostStack|WorkingDirectory=$PWD|g" config/ghoststack.service
fi

# Copy service file
sudo cp config/ghoststack.service /etc/systemd/system/

# Reload systemd and enable
sudo systemctl daemon-reload
sudo systemctl enable ghoststack.service

echo "[+] GhostStack service installed and enabled to start on boot."
echo "[*] To start now, run: sudo systemctl start ghoststack.service"
echo "[*] To view logs, run: sudo journalctl -u ghoststack.service -f"
