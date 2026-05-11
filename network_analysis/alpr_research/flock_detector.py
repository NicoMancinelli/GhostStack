import scapy.all as scapy
from scapy.layers.dot11 import Dot11ProbeReq
import time
import logging

# GhostStack: ALPR Research - Passive Flock Camera Detector
# 
# Based on research from projects like 'flock-you', Flock Safety cameras 
# can often be identified by their passive WiFi behavior, specifically 
# probe requests or hardcoded OUIs.
#
# NOTE: Requires a WiFi adapter in monitor mode (e.g., ALFA AWUS036ACM).

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [FLOCK_DETECTOR] - %(message)s')

# Known MAC prefixes associated with Flock/Hanwha/Industrial hardware
# This list is for research purposes and should be expanded based on local observations.
FLOCK_OUIs = [
    "00:16:6c", # Samsung/Hanwha (Commonly used in Flock hardware)
    "00:09:18", # Samsung Techwin
    "c4:2f:90", # Hanwha Techwin
]

# Flock cameras have been observed probing for specific SSIDs or using wildcard probes
FLOCK_PROBE_KEYWORDS = ["flock", "falcon", "raven"]

def packet_callback(pkt):
    if pkt.haslayer(Dot11ProbeReq):
        mac = pkt.addr2.lower()
        ssid = pkt.info.decode(errors='ignore').lower() if pkt.info else ""
        
        # Check OUI
        is_flock_oui = any(mac.startswith(oui) for oui in FLOCK_OUIs)
        
        # Check SSID Keywords
        is_flock_ssid = any(keyword in ssid for keyword in FLOCK_PROBE_KEYWORDS)

        if is_flock_oui or is_flock_ssid:
            logging.info(f"[!] POTENTIAL FLOCK CAMERA DETECTED")
            logging.info(f"    MAC: {mac}")
            logging.info(f"    SSID: '{ssid}'")
            logging.info(f"    Signal Strength: {pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else 'N/A'} dBm")

def main():
    interface = "wlan0mon" # Change to your monitor mode interface
    logging.info(f"[*] Starting passive Flock detector on {interface}...")
    logging.info("[*] Listening for Probe Requests and matching known OUIs...")
    
    try:
        scapy.sniff(iface=interface, prn=packet_callback, store=0)
    except Exception as e:
        logging.error(f"Error: {e}")
        logging.info("Ensure your interface is in MONITOR mode: 'sudo airmon-ng start wlan0'")

if __name__ == "__main__":
    main()
