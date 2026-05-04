import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    # Caminho absoluto da pasta onde estão os scripts (considerando o pacote do usuário no Pi)
    base_dir = '/home/ubuntu/AGRI-Scout_Modif'
    
    return LaunchDescription([
        # 1. Lança o LiDAR nativamente como um Nó do ROS 2
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_node',
            output='log', # Evita poluir a tela com mensagens do Lidar
            parameters=[{
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 115200,
                'frame_id': 'laser',
                'angle_compensate': True,
                'scan_mode': 'Standard'
            }]
        ),
        
        # 2. Executa o Script em Python puro do IMU Artemis no plano de fundo
        ExecuteProcess(
            cmd=['python3', 'Luiz_2304_testeArtemis.py'],
            cwd=base_dir,
            output='screen', # Mostra o Roll, Pitch e Yaw na tela principal
            emulate_tty=True # Mantém o print formatado perfeitamente
        )
    ])
