#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import time
import psutil
import os

class SystemMonitor(Node):
    def __init__(self):
        super().__init__('hardware_system_monitor')
        self.get_logger().info("Iniciando Monitor de Sistema / Bateria...")
        self.timer = self.create_timer(2.0, self.timer_callback)

    def get_cpu_temp(self):
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read()) / 1000.0
            return temp
        except FileNotFoundError:
            return None

    def get_battery_info(self):
        # Caso o robô possua uma interface de bateria no sysfs (comum em setups com UPS x728 ou semelhantes)
        # Placeholder para leitura de bateria.
        # Em robôs ROS 2, frequentemente isso vem de um tópico, por ex: /battery_state
        # mas aqui tentamos algo a nível de SO ou script custom.
        try:
            with open("/sys/class/power_supply/BAT0/capacity", "r") as f:
                cap = f.read().strip()
            return f"{cap}%"
        except FileNotFoundError:
            return "Indisponível (Sem /sys/.../BAT0)"

    def timer_callback(self):
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        cpu_temp = self.get_cpu_temp()
        battery = self.get_battery_info()

        print("\n========================================")
        print("💻 System Monitor (Raspberry Pi 4):")
        print(f"🔹 CPU Uso       : {cpu_usage:.1f} %")
        if cpu_temp is not None:
            print(f"🔹 CPU Temp      : {cpu_temp:.1f} °C")
            if cpu_temp > 75.0:
                print("   ⚠️ ALERTA: Temperatura Alta!")
        else:
            print("🔹 CPU Temp      : Não foi possível ler")
            
        print(f"🔹 Memória RAM   : {mem.used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB ({mem.percent}%)")
        print(f"🔹 Bateria       : {battery}")
        print("========================================")

def main(args=None):
    rclpy.init(args=args)
    node = SystemMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Monitor encerrado pelo usuário.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
