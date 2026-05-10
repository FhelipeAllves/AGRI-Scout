#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from rclpy.qos import QoSProfile, ReliabilityPolicy
from cv_bridge import CvBridge
import cv2
import numpy as np
import serial
import time
import math

class AgriDemoHunter(Node):
    def __init__(self):
        super().__init__('agri_demo_hunter')
        
        # --- 1. SERIAL & STATE MACHINE CONFIGURATION ---
        self.serial_port = '/dev/ttyACM0'
        self.baud_rate = 9600
        self.state = "SEARCHING"
        self.lost_frames = 0
        
        # Target Color HSV (Bright Red/Orange - Adjust for Demo)
        self.lower_color = np.array([0, 120, 70])
        self.upper_color = np.array([10, 255, 255])
        
        # How close it needs to be to harvest (Object Area on Screen)
        # Adjusted to 15000 because new camera resolution has 4x fewer pixels
        self.harvest_area_threshold = 15000 
        
        # --- 2. SERIAL COMMUNICATION (ARDUINO) ---
        try:
            self.robot = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            time.sleep(2)
            self.get_logger().info("🔥 Connected to Arduino Motors!")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")
            raise SystemExit

        self.last_command = ""
        self.last_cmd_time = time.time()

        # --- 3. LIDAR SAFETY OVERRIDE ---
        self.obstacle_ahead = False
        qos_lidar = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, depth=10)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_cb, qos_lidar)

        # --- 4. CAMERA VISION ---
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(Image, '/image_raw', self.image_cb, 1)
        
        self.get_logger().info("🎯 Hunter System Online! Scanning field...")

    def send_cmd(self, cmd):
        # Send only if changed, or send "heartbeat" every 0.3s
        if cmd != self.last_command or (time.time() - self.last_cmd_time) > 0.3:
            self.robot.write((cmd + '\n').encode('utf-8'))
            self.last_command = cmd
            self.last_cmd_time = time.time()

    def scan_cb(self, msg):
        # RPLidar scans 0 to 360. Front is usually 0 or 180.
        # Assuming Front = 0 degrees (+/- 20 degrees).
        # Convert array to filter 20 degrees left and right
        ranges = msg.ranges
        num_points = len(ranges)
        
        if num_points < 100: return
        
        # Get front-facing "slice"
        front_slice = ranges[:20] + ranges[-20:]
        
        # Filter garbage (0.0 m)
        valid_ranges = [r for r in front_slice if 0.1 < r < msg.range_max]
        
        if valid_ranges:
            min_dist = min(valid_ranges)
            if min_dist < 0.4:  # Less than 40 centimeters!
                self.obstacle_ahead = True
            else:
                self.obstacle_ahead = False

    def image_cb(self, msg):
        if self.state == "HARVESTING":
            return # If already found, don't process vision

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"cv_bridge error: {e}")
            return

        h, w, _ = cv_image.shape
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        # Find Color (Thresholding)
        mask = cv2.inRange(hsv, self.lower_color, self.upper_color)
        
        # Get the largest contour (Our Flag/Token)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        target_found = False
        target_x, target_y, target_area = 0, 0, 0
        
        if contours:
            c = max(contours, key=cv2.contourArea)
            target_area = cv2.contourArea(c)
            
            if target_area > 500: # Ignore garbage false-positive pixels
                M = cv2.moments(c)
                if M["m00"] != 0:
                    target_x = int(M["m10"] / M["m00"])
                    target_y = int(M["m01"] / M["m00"])
                    target_found = True
                    cv2.drawContours(cv_image, [c], -1, (0, 255, 0), 3)
                    cv2.circle(cv_image, (target_x, target_y), 5, (255, 0, 0), -1)

        # ====== STATE MACHINE DECISION ======
        
        # 1. EMERGENCY STOP (LIDAR)
        if self.obstacle_ahead:
            self.send_cmd("X")
            self.get_logger().warn("OBSTACLE AHEAD! Brakes engaged.")
            cv2.putText(cv_image, "OBSTACLE WARNING/LIDAR", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        else:
            # 2. SEARCH MODE (Dog spinning on axis)
            if not target_found:
                self.lost_frames += 1
                if self.lost_frames > 15: # Lost for 0.5 seconds? Spin to search!
                    self.state = "SEARCHING"
                    self.send_cmd("R20") # Turn like a tank slowly
                    cv2.putText(cv_image, "[STATE] SEARCHING", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # 3. LOCK-ON AND APPROACH MODE
            else:
                self.lost_frames = 0
                
                # If area is huge, arrived at destination!
                if target_area > self.harvest_area_threshold:
                    self.state = "HARVESTING"
                    self.get_logger().info("🔥 TARGET HIT!! INITIATING PROBE...")
                    self.send_cmd("X")
                    self.harvest_routine() # Trigger synchronous mechanical routine
                    return
                
                self.state = "TRACKING"
                # Screen error: Left(-) or Right(+)
                center_x = w // 2
                error_x = target_x - center_x
                
                cv2.putText(cv_image, f"[STATE] TRACKING (Erro: {error_x}) Area: {int(target_area)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Rustic Proportional Controller
                if error_x < -80:   # Too far left
                    self.send_cmd("L20")
                elif error_x > 80:  # Too far right
                    self.send_cmd("R20")
                else:               # Centered, accelerate!
                    self.send_cmd("F25") # Forward
                    
        # --- HEADLESS MODE (For SSH without visual screen) ---
        # Temporarily removed cv2.imshow() to avoid crashing on headless terminal (X11 Header)
        # cv2.imshow("DEMO HUNTER VIEW", cv_image)
        # cv2.waitKey(1)

    def harvest_routine(self):
        # Lock wheels
        self.send_cmd("X")
        time.sleep(1)
        
        self.get_logger().info("👇 Probe DESCENDING (-11000 Steps)")
        self.robot.write(b"S-11000\n")
        
        # Wait physical time for movement completion
        # Tip: The loop blocks here intentionally for Demo
        time.sleep(15) 
        
        self.get_logger().info("👆 Probe ASCENDING (11000 Steps)")
        self.robot.write(b"S11000\n")
        time.sleep(15)
        
        self.get_logger().info("✅ MISSION COMPLETE! Returning to search mode.")
        # Return to hunt in case multiple flags are scattered
        self.state = "SEARCHING"
        self.lost_frames = 50

def main(args=None):
    rclpy.init(args=args)
    node = AgriDemoHunter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node terminated by developer.")
        node.send_cmd("X")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
