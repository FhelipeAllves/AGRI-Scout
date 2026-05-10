#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import time
import psutil
import os

class SystemMonitor(Node):
    def __init__(self):
        super().__init__('hardware_system_monitor')
        self.get_logger().info("Starting System / Battery Monitor...")
        self.timer = self.create_timer(2.0, self.timer_callback)

    def get_cpu_temp(self):
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read()) / 1000.0
            return temp
        except FileNotFoundError:
            return None

    def get_battery_info(self):
        # If the robot has a sysfs battery interface (common with UPS x728 or similar)
        # Placeholder for battery reading.
        # In ROS 2 robots, this often comes from a topic, e.g.: /battery_state
        # but here we try OS-level or custom script.
        try:
            with open("/sys/class/power_supply/BAT0/capacity", "r") as f:
                cap = f.read().strip()
            return f"{cap}%"
        except FileNotFoundError:
            return "Unavailable (No /sys/.../BAT0)"

    def timer_callback(self):
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        cpu_temp = self.get_cpu_temp()
        battery = self.get_battery_info()

        print("\n========================================")
        print("💻 System Monitor (Raspberry Pi 4):")
        print(f"🔹 CPU Usage     : {cpu_usage:.1f} %")
        if cpu_temp is not None:
            print(f"🔹 CPU Temp      : {cpu_temp:.1f} °C")
            if cpu_temp > 75.0:
                print("   ⚠️ WARNING: High Temperature!")
        else:
            print("🔹 CPU Temp      : Could not read")
            
        print(f"🔹 RAM Memory    : {mem.used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB ({mem.percent}%)")
        print(f"🔹 Battery       : {battery}")
        print("========================================")

def main(args=None):
    rclpy.init(args=args)
    node = SystemMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Monitor terminated by user.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
