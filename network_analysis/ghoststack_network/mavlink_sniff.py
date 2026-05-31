from scapy.all import sniff
from scapy.layers.inet import UDP

from ghoststack.events import format_threat
from ghoststack.mavlink import MSG_HEARTBEAT, extract_gps, parse_frame

# GhostStack: Network Layer - MAVLink v1/v2 Sniffer (real GPS from telemetry)


def mavlink_callback(pkt):
    if not (pkt.haslayer(UDP) and pkt[UDP].dport == 14550):
        return
    raw = bytes(pkt[UDP].payload)
    frame = parse_frame(raw)
    if not frame:
        return

    gps = extract_gps(frame)
    if gps:
        alt_note = f", alt={gps.alt_m:.1f}m" if gps.alt_m is not None else ""
        print(
            format_threat(
                f"{gps.source}: SysID={frame.sys_id}, CompID={frame.comp_id}{alt_note}",
                lat=gps.lat,
                lon=gps.lon,
            )
        )
        return

    if frame.msg_id == MSG_HEARTBEAT:
        print(f"[*] HEARTBEAT: SysID={frame.sys_id}, CompID={frame.comp_id}")
    else:
        print(f"[*] MAVLINK: MsgID={frame.msg_id}, SysID={frame.sys_id}")


def main():
    print("[*] Monitoring MAVLink traffic on UDP/14550 (GPS from GLOBAL_POSITION_INT / GPS_RAW_INT)...")
    sniff(filter="udp port 14550", prn=mavlink_callback, store=0)


if __name__ == "__main__":
    main()
