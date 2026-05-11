from scapy.all import *
from scapy.layers.inet import UDP
import struct

# GhostStack: Network Layer - MAVLink V2 Sniffer
# Extracts Heartbeat data from unencrypted MAVLink over UDP

def mavlink_callback(pkt):
    if pkt.haslayer(UDP) and pkt[UDP].dport == 14550:
        raw = bytes(pkt[UDP].payload)
        if len(raw) > 10 and raw[0] == 0xfd: # MAVLink V2 STX
            # Extract MsgID (3 bytes starting at index 7)
            # Use struct to unpack and handle the 3-byte msg_id
            msg_id = struct.unpack('<I', raw[7:10] + b'\x00')[0]
            sys_id = raw[5]
            comp_id = raw[6]

            if msg_id == 0: # Heartbeat
                print(f"[!] HEARTBEAT: SysID={sys_id}, CompID={comp_id}")
            else:
                print(f"[*] MAVLINK: MsgID={msg_id}, SysID={sys_id}")

def main():
    print("[*] Monitoring MAVLink traffic on UDP/14550...")
    sniff(filter='udp port 14550', prn=mavlink_callback, store=0)

if __name__ == '__main__':
    main()
