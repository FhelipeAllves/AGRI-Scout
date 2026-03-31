#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import time
import sys
import tty
import termios

class MotorsTester(Node):
    def __init__(self):
        super().__init__('hardware_test_motors')
        self.get_logger().info("Iniciando Teste dos Motores...")
        self.get_logger().info("CONTROLES: Opere usando as teclas W (frente), S (trás), A (esquerda), D (direita). Espaço para parar. Q para sair.")
        
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        self.odom_data = None
        
        self.timer = self.create_timer(1.0, self.status_callback)

    def odom_callback(self, msg):
        self.odom_data = msg

    def status_callback(self):
        if self.odom_data:
            v_lin = self.odom_data.twist.twist.linear.x
            v_ang = self.odom_data.twist.twist.angular.z
            print(f"\r[Odometry] V_Linear: {v_lin:.2f} m/s | V_Angular: {v_ang:.2f} rad/s", end="")

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main(args=None):
    rclpy.init(args=args)
    node = MotorsTester()
    
    twist = Twist()
    speed = 0.2
    turn = 0.5
    
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
            key = get_key()
            if key == 'w':
                twist.linear.x = speed
                twist.angular.z = 0.0
            elif key == 's':
                twist.linear.x = -speed
                twist.angular.z = 0.0
            elif key == 'a':
                twist.linear.x = 0.0
                twist.angular.z = turn
            elif key == 'd':
                twist.linear.x = 0.0
                twist.angular.z = -turn
            elif key == ' ':
                twist.linear.x = 0.0
                twist.angular.z = 0.0
            elif key == 'q':
                break
                
            node.pub.publish(twist)
            print(f"\n[Command] V_Linear: {twist.linear.x:.2f} | V_Angular: {twist.angular.z:.2f}")

    except Exception as e:
        print(e)
    finally:
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        node.pub.publish(twist)
        time.sleep(0.1)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
