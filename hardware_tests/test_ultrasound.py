#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
import time

class UltrasoundTester(Node):
    def __init__(self):
        super().__init__('hardware_test_ultrasound')
        self.get_logger().info("Iniciando Teste dos Sensores Ultrassônicos...")
        
        self.readings = {
            'front': None,
            'left': None,
            'right': None,
            'rear': None
        }
        
        self.create_subscription(Range, '/ultrasonic/front', lambda m: self.callback('front', m), 10)
        self.create_subscription(Range, '/ultrasonic/left', lambda m: self.callback('left', m), 10)
        self.create_subscription(Range, '/ultrasonic/right', lambda m: self.callback('right', m), 10)
        self.create_subscription(Range, '/ultrasonic/rear', lambda m: self.callback('rear', m), 10)
        
        self.timer = self.create_timer(1.0, self.timer_callback)

    def callback(self, position, msg):
        self.readings[position] = msg.range

    def timer_callback(self):
        print("\n========================================")
        print(f"🦇 Leituras Ultrassônicas:")
        
        for pos, val in self.readings.items():
            if val is not None:
                print(f"🔹 {pos.capitalize():<6} : {val:.3f} m")
            else:
                print(f"🔹 {pos.capitalize():<6} : Aguardando dados...")
                
        print("========================================")

def main(args=None):
    rclpy.init(args=args)
    node = UltrasoundTester()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Teste dos Sensores Ultrassônicos encerrado pelo usuário.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
