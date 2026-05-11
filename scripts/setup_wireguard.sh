#!/bin/bash
# GhostStack: WireGuard Security Tunnel Setup
#
# Configures a basic WireGuard VPN interface to ensure the GhostStack
# dashboard and control plane are only accessible over an encrypted tunnel.

set -e

echo "[*] GhostStack WireGuard Setup"

if ! command -v wg &> /dev/null; then
    echo "[*] Installing WireGuard..."
    sudo apt-get update && sudo apt-get install -y wireguard
fi

WG_DIR="/etc/wireguard"
IFACE="wg0"

if [ -f "$WG_DIR/$IFACE.conf" ]; then
    echo "[-] WireGuard interface $IFACE already exists."
    exit 0
fi

echo "[*] Generating keys..."
umask 077
SERVER_PRIVKEY=$(wg genkey)
SERVER_PUBKEY=$(echo "$SERVER_PRIVKEY" | wg pubkey)

CLIENT_PRIVKEY=$(wg genkey)
CLIENT_PUBKEY=$(echo "$CLIENT_PRIVKEY" | wg pubkey)

echo "[*] Creating server config..."
sudo bash -c "cat > $WG_DIR/$IFACE.conf" <<EOF
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = $SERVER_PRIVKEY

[Peer]
# Operator Client
PublicKey = $CLIENT_PUBKEY
AllowedIPs = 10.0.0.2/32
EOF

echo "[*] Generating client config (save this to your operator device)..."
cat > ghoststack_client.conf <<EOF
[Interface]
Address = 10.0.0.2/24
PrivateKey = $CLIENT_PRIVKEY

[Peer]
PublicKey = $SERVER_PUBKEY
Endpoint = <GHOSTSTACK_PUBLIC_IP>:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
EOF

sudo systemctl enable wg-quick@$IFACE
sudo systemctl start wg-quick@$IFACE

echo "[+] WireGuard tunnel active on 10.0.0.1"
echo "[+] Client config saved to ghoststack_client.conf"
echo "[!] IMPORTANT: Configure your firewall to only allow access to port 5000 (Dashboard) from the wg0 interface (10.0.0.0/24)."
