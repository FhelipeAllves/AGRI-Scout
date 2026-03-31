#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix
import time

class ImuGpsTester(Node):
    def __init__(self):
        super().__init__('hardware_test_imu_gps')
        self.get_logger().info("Iniciando Teste de IMU e GPS...")
        
        self.imu_data = None
        self.gps_data = None
        
        self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        self.create_subscription(NavSatFix, '/gps/fix', self.gps_callback, 10)
        
        self.timer = self.create_timer(1.0, self.timer_callback)

    def imu_callback(self, msg):
        self.imu_data = msg

    def gps_callback(self, msg):
        self.gps_data = msg

    def timer_callback(self):
        print("\n========================================")
        print("🧭 Status do IMU e GPS:")
        
        if self.imu_data:
            q = self.imu_data.orientation
            av = self.imu_data.angular_velocity
            la = self.imu_data.linear_acceleration
            print(f"🔹 IMU Orientação  : (x:{q.x:.2f}, y:{q.y:.2f}, z:{q.z:.2f}, w:{q.w:.2f})")
            print(f"🔹 IMU Ang. Vel.   : (x:{av.x:.2f}, y:{av.y:.2f}, z:{av.z:.2f})")
            print(f"🔹 IMU Lin. Accel. : (x:{la.x:.2f}, y:{la.y:.2f}, z:{la.z:.2f})")
        else:
            print("🔹 IMU             : Aguardando dados...")
            
        print("----------------------------------------")
            
        if self.gps_data:
            lat = self.gps_data.latitude
            lon = self.gps_data.longitude
            alt = self.gps_data.altitude
            print(f"🔹 GPS Latitude    : {lat:.6f}")
            print(f"🔹 GPS Longitude   : {lon:.6f}")
            print(f"🔹 GPS Altitude    : {alt:.2f} m")
        else:
            print("🔹 GPS             : Aguardando dados...")
            
        print("========================================")

def main(args=None):
    rclpy.init(args=args)
    node = ImuGpsTester()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Teste de IMU/GPS encerrado pelo usuário.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
