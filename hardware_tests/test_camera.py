#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import time
import os

class CameraTester(Node):
    def __init__(self):
        super().__init__('hardware_test_camera')
        self.get_logger().info("Iniciando Teste da Câmera (RGB e Profundidade)...")
        
        self.sub_rgb = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.rgb_callback,
            10)
            
        self.sub_depth = self.create_subscription(
            Image,
            '/camera/depth_image',
            self.depth_callback,
            10)
            
        self.rgb_count = 0
        self.depth_count = 0
        
        self.last_rgb_info = None
        self.last_depth_info = None
        
        self.start_time = time.time()
        self.last_print_time = time.time()

    def rgb_callback(self, msg):
        self.rgb_count += 1
        self.last_rgb_info = f"{msg.width}x{msg.height} ({msg.encoding})"
        self._check_print()

    def depth_callback(self, msg):
        self.depth_count += 1
        self.last_depth_info = f"{msg.width}x{msg.height} ({msg.encoding})"
        self._check_print()
        
    def _check_print(self):
        current_time = time.time()
        if current_time - self.last_print_time >= 1.0:
            rgb_hz = self.rgb_count / (current_time - self.start_time)
            depth_hz = self.depth_count / (current_time - self.start_time)
            
            print("\n========================================")
            print(f"📷 Status da Câmera:")
            print(f"🔹 RGB Taxa / Formato        : {rgb_hz:.2f} Hz | {self.last_rgb_info or 'N/A'}")
            print(f"🔹 Profundidade Taxa         : {depth_hz:.2f} Hz | {self.last_depth_info or 'N/A'}")
            print("========================================")
            
            self.rgb_count = 0
            self.depth_count = 0
            self.start_time = current_time
            self.last_print_time = current_time

def main(args=None):
    rclpy.init(args=args)
    node = CameraTester()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Teste da Câmera encerrado pelo usuário.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
