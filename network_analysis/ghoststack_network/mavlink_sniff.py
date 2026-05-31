import struct

from scapy.all import sniff
from scapy.layers.inet import UDP

from ghoststack.events import format_threat

# GhostStack: Network Layer - MAVLink V2 Sniffer


def mavlink_callback(pkt):
    if pkt.haslayer(UDP) and pkt[UDP].dport == 14550:
        raw = bytes(pkt[UDP].payload)
        if len(raw) > 10 and raw[0] == 0xFD:
            msg_id = struct.unpack("<I", raw[7:10] + b"\x00")[0]
            sys_id = raw[5]
            comp_id = raw[6]

            if msg_id == 0:
                from ghoststack.config_loader import load_targets

                center = load_targets().get("default_map_center", {})
                print(
                    format_threat(
                        f"HEARTBEAT: SysID={sys_id}, CompID={comp_id}",
                        lat=float(center.get("lat", 37.7749)),
                        lon=float(center.get("lon", -122.4194)),
                    )
                )
            else:
                print(f"[*] MAVLINK: MsgID={msg_id}, SysID={sys_id}")


def main():
    print("[*] Monitoring MAVLink traffic on UDP/14550...")
    sniff(filter="udp port 14550", prn=mavlink_callback, store=0)


if __name__ == "__main__":
    main()
