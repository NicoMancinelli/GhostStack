import logging
import os

import scapy.all as scapy
from scapy.layers.dot11 import Dot11Beacon, Dot11ProbeResp

from ghoststack.config_loader import load_targets
from ghoststack.events import format_threat

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [REMOTE_ID] - %(message)s")


def packet_callback(pkt):
    if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
        try:
            ssid = pkt.info.decode(errors="ignore") if pkt.info else "Hidden"
            mac = pkt.addr2
            if "Drone" in ssid or "UAV" in ssid or "RemoteID" in ssid:
                targets = load_targets()
                center = targets.get("default_map_center", {})
                lat = float(center.get("lat", 37.7749))
                lon = float(center.get("lon", -122.4194))
                logging.info(
                    format_threat(
                        f"Potential RemoteID Broadcast: MAC={mac}, SSID='{ssid}'",
                        lat=lat,
                        lon=lon,
                    )
                )
        except Exception:
            pass


def main():
    targets = load_targets()
    interface = os.environ.get(
        "GHOSTSTACK_WIFI_IFACE", targets.get("wifi_monitor_interface", "wlan0mon")
    )
    logging.info(f"[*] Starting passive Remote ID sniffer on {interface}...")
    try:
        scapy.sniff(iface=interface, prn=packet_callback, store=0)
    except Exception as exc:
        logging.error(f"Error: {exc}")
        logging.info("Ensure interface is in MONITOR mode: 'sudo airmon-ng start wlan0'")


if __name__ == "__main__":
    main()
