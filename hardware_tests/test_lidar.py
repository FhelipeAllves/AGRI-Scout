#!/usr/bin/env python3
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data

class LidarTester(Node):
    def __init__(self):
        super().__init__('hardware_test_lidar')
        self.get_logger().info("Starting LiDAR Test...")
        
        # The critical fix: Using Sensor Data QoS profile
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )
        
        self.msg_count = 0
        self.start_time = time.time()
        self.last_print_time = time.time()

    def scan_callback(self, msg):
        self.msg_count += 1
        current_time = time.time()
        
        # Print status every 1 second
        if current_time - self.last_print_time >= 1.0:
            hz = self.msg_count / (current_time - self.start_time)
            
            # Filter valid points (not inf and not nan)
            valid_ranges = [r for r in msg.ranges if msg.range_min <= r <= msg.range_max]
            
            num_points = len(msg.ranges)
            num_valid = len(valid_ranges)
            
            if num_valid > 0:
                min_dist = min(valid_ranges)
                max_dist = max(valid_ranges)
            else:
                min_dist = 0.0
                max_dist = 0.0

            print("\n========================================")
            print("📡 LiDAR Status:")
            print(f"🔹 Publish Rate : {hz:.2f} Hz")
            print(f"🔹 Total Points : {num_points}")
            print(f"🔹 Valid Points : {num_valid}")
            print(f"🔹 Min Distance : {min_dist:.2f} m")
            print(f"🔹 Max Distance : {max_dist:.2f} m")
            print("========================================")
            
            self.msg_count = 0
            self.start_time = current_time
            self.last_print_time = current_time

def main(args=None):
    rclpy.init(args=args)
    node = LidarTester()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("LiDAR test terminated by user.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
