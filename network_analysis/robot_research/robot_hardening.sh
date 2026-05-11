#!/bin/bash

# GhostStack: Defensive Research - Robotic Hardening Script
# 
# Inspired by Benn Jordan's remediation research. 
# Run this script ON the target robot (e.g., Unitree Go2) to secure it.

set -e

echo "[*] GhostStack: Starting Robotic Hardening Protocol..."

# 1. Update SSH Passwords
echo "[*] Securing SSH access..."
echo "Enter NEW password for current user:"
passwd

# 2. Disable Hidden WiFi Backdoor (Unitree Specific)
# Many robots use hostapd for the internal AP.
if [ -f "/etc/hostapd/hostapd.conf" ]; then
    echo "[!] Detected hidden AP configuration. Disabling..."
    sudo systemctl stop hostapd || true
    sudo systemctl disable hostapd || true
    # Optionally comment out the SSID/WPA config
    sudo sed -i 's/^ssid=/#ssid=/' /etc/hostapd/hostapd.conf
fi

# 3. Secure MAVLink Ports
# If using unencrypted MAVLink over UDP, we recommend wrapping in a VPN (WireGuard).
# For now, we block external MAVLink access except for known ground station IPs.
if command -v iptables &> /dev/null; then
    echo "[*] Hardening Network Stack (iptables)..."
    # Block MAVLink UDP 14550 from external interfaces, allow local
    sudo iptables -A INPUT -p udp --dport 14550 -i lo -j ACCEPT
    # Add your GCS IP here if needed:
    # sudo iptables -A INPUT -p udp --dport 14550 -s <GCS_IP> -j ACCEPT
    sudo iptables -A INPUT -p udp --dport 14550 -j DROP
fi

# 4. Check for Cloud Backdoors
# Look for common cloud-syncing agents
for agent in "unitree_cloud" "dji_service"; do
    if pgrep -f "$agent" > /dev/null; then
        echo "[!] Found cloud agent: $agent. Killing process..."
        sudo pkill -f "$agent" || true
    fi
done

echo "[+] Hardening Complete. Robotic system is now significantly more resilient."
