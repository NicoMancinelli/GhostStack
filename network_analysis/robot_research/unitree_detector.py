import scapy.all as scapy
from scapy.layers.dot11 import Dot11Beacon, Dot11ProbeResp
import logging
import re

# GhostStack: Quadruped Vulnerability Research
# 
# Based on research (e.g. Benn Jordan's "Robot Dogs Are A Security Nightmare"),
# Unitree and similar commercial robots often have hidden Wi-Fi access points
# acting as unauthenticated backdoors, and broadcast unencrypted MAVLink over UDP.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [QUADRUPED_DETECT] - %(message)s')

# Known MAC prefixes associated with Unitree or typical robotic compute modules
UNITREE_OUIs = [
    "00:0c:43", # Ralink (Common in cheap embedded WiFi)
    "b8:27:eb", # Raspberry Pi Foundation (often used internally)
    "dc:a6:32", # Raspberry Pi (newer)
]

def analyze_beacon(pkt):
    if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
        mac = pkt.addr2.lower()
        ssid = pkt.info.decode(errors='ignore') if pkt.info else ""
        
        # Detect hidden SSIDs (length > 0 but containing null bytes)
        is_hidden = len(ssid) > 0 and all(c == '\x00' for c in ssid)
        
        # Check OUI
        is_suspicious_oui = any(mac.startswith(oui) for oui in UNITREE_OUIs)

        if "unitree" in ssid.lower() or (is_hidden and is_suspicious_oui):
            logging.info(f"[!] POTENTIAL ROBOT BACKDOOR AP DETECTED")
            logging.info(f"    MAC: {mac}")
            logging.info(f"    SSID: '{ssid if not is_hidden else '<HIDDEN>'}'")
            logging.info(f"    Signal Strength: {pkt.dBm_AntSignal if hasattr(pkt, 'dBm_AntSignal') else 'N/A'} dBm")
            logging.info(f"    [!] ACTION: Launch MAVLink sniffer to monitor unencrypted UDP traffic.")

def main():
    interface = "wlan0mon" # Change to your monitor mode interface
    logging.info(f"[*] Starting Quadruped Robot backdoor detector on {interface}...")
    logging.info("[*] Listening for Hidden APs and known robotic OUIs...")
    
    try:
        scapy.sniff(iface=interface, prn=analyze_beacon, store=0)
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()
