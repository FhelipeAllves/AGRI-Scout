#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import sys

# ==========================================
# ROS 2 SERIAL BRIDGE NODE
# ==========================================
class AgriSerialBridge(Node):
    def __init__(self):
        super().__init__('agri_serial_bridge')
        
        # Subscribe to the command topic
        self.subscription = self.create_subscription(
            String,
            'agri_commands',
            self.command_callback,
            10
        )
        
        self.serial_port = '/dev/ttyACM0'
        self.baud_rate = 9600
        
        # Initialize Serial Connection
        try:
            self.robot = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.get_logger().info(f"Connected to Arduino on {self.serial_port}")
        except serial.SerialException:
            self.get_logger().error(f"Failed to connect to {self.serial_port}")
            sys.exit(1)
            
        # Timer to read feedback from Arduino
        self.timer = self.create_timer(0.05, self.read_serial_callback)

    def command_callback(self, msg):
        # Add newline and send directly to Arduino
        command = f"{msg.data}\n"
        self.robot.write(command.encode('utf-8'))
        self.get_logger().debug(f"Sent to hardware: {msg.data}")

    def read_serial_callback(self):
        # Read incoming logs from Arduino and publish to ROS console
        if self.robot.in_waiting > 0:
            try:
                line = self.robot.readline().decode('utf-8').strip()
                if line:
                    self.get_logger().info(f"[ARDUINO]: {line}")
            except UnicodeDecodeError:
                pass

def main(args=None):
    rclpy.init(args=args)
    node = AgriSerialBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Failsafe: Send hard stop command before shutting down
        if hasattr(node, 'robot') and node.robot.is_open:
            node.robot.write("X\n".encode('utf-8'))
            node.robot.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
