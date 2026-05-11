import socket
import sys

# GhostStack: Robotic Research - Service Mapper
#
# Identifies common robotic middleware and control ports to determine 
# the 'Stack' of the target platform (ROS 2, MAVLink, Zenoh, etc.)

ROBOT_PORTS = {
    22: "SSH (Management)",
    14550: "MAVLink (Telemetry/Control)",
    14540: "MAVLink (SITL/Offboard)",
    7400: "ROS 2 / DDS (Discovery/Data)",
    7401: "ROS 2 / DDS (Discovery/Data)",
    8000: "Web Interface (Management)",
    8080: "Web Interface / Video Stream",
    9090: "rosbridge (WebSocket JSON API)",
    7447: "Zenoh (Middleware)",
    23: "Telnet (Legacy/Debug Backdoor)",
}

def map_robot_services(target_ip):
    print(f"[*] Mapping robotic services for {target_ip}...")
    
    for port, desc in ROBOT_PORTS.items():
        try:
            # Use a short timeout for efficiency
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((target_ip, port))
            
            if result == 0:
                print(f"    [+] Port {port} OPEN: {desc}")
            
            # Also check for UDP services (MAVLink/DDS)
            # (Simplified check: UDP is harder to verify without protocol-specific handshakes)
            
            sock.close()
        except Exception as e:
            pass

    print("\n[*] Mapping complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 robot_service_mapper.py <target_ip>")
        sys.exit(1)
    
    map_robot_services(sys.argv[1])
