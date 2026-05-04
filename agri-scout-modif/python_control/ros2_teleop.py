#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sys
import termios
import tty
import select

# ==========================================
# ROS 2 KEYBOARD TELEOPERATION NODE
# ==========================================
class AgriTeleopController(Node):
    def __init__(self):
        super().__init__('agri_teleop_controller')
        self.publisher_ = self.create_publisher(String, 'agri_commands', 10)
        self.move_speed = 20

        self.print_menu()
        self.timer = self.create_timer(0.05, self.teleop_loop)

    def print_menu(self):
        menu = """
=== AGRI-SCOUT ROS 2 TELEOPERATION ===
W : Forward       I : Probe Down
S : Backward      K : Probe Up
A : Turn Left
D : Turn Right
SPACE : Stop All  Q : Quit
======================================
"""
        print(menu)

    def get_key(self):
        # Non-blocking keyboard input reader
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                key = sys.stdin.read(1)
            else:
                key = ''
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key.upper()

    def teleop_loop(self):
        key = self.get_key()
        if not key:
            return

        msg = String()
        
        # Map keys to Arduino commands
        if key == 'W':
            print("\r[MOVE] Forward                ", end='')
            msg.data = f"F{self.move_speed}"
        elif key == 'S':
            print("\r[MOVE] Backward               ", end='')
            msg.data = f"B{self.move_speed}"
        elif key == 'A':
            print("\r[MOVE] Left                   ", end='')
            msg.data = f"L{self.move_speed}"
        elif key == 'D':
            print("\r[MOVE] Right                  ", end='')
            msg.data = f"R{self.move_speed}"
        elif key == ' ' or key == 'P':
            print("\r[STOP] Stopping Wheels        ", end='')
            msg.data = "X"
        elif key == 'I':
            print("\r[PROBE] Moving DOWN continuously...   ", end='')
            msg.data = "D"
        elif key == 'K':
            print("\r[PROBE] Moving UP continuously...     ", end='')
            msg.data = "U"
        elif key == 'Q':
            print("\nExiting and stopping robot...")
            msg.data = "X"
            self.publisher_.publish(msg)
            sys.exit(0)
        else:
            return

        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = AgriTeleopController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
