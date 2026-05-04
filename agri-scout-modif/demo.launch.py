import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    # Caminho do Cérebro Python do Robô
    base_dir = '/home/ubuntu/AGRI-Scout_Modif'
    
    return LaunchDescription([
       # 1. ATIVAR A RETINA (Câmera USB V4L2)
        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            name='v4l2_camera_node',
            output='screen', # Mude para 'screen' temporariamente para ver se há erros
            parameters=[{
                'image_size': [320, 240], 
                'time_per_frame': [1, 10], # Aumentei para 10 FPS, pois com MJPG a Pi aguenta rindo!
                'pixel_format': 'mjpeg',   # A MÁGICA: Puxa o bloco [2] do hardware da câmera
            }]
        ),
        
        # 2. ATIVAR O ESCUDO FRONTAL (LiDAR)
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_node',
            output='log',
            parameters=[{
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 115200,
                'frame_id': 'laser',
                'angle_compensate': True,
                'scan_mode': 'Standard'
            }]
        ),
        ExecuteProcess(
            cmd=['python3', 'python_control/agri_line_follower.py'],
            cwd=base_dir,
            output='screen', # Fundamental para ler os Logs do "Alvo Atingido"
            emulate_tty=True
        )
    ])