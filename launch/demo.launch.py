import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

def generate_launch_description():
    # Python Brain Path
    base_dir = '/home/ubuntu/AGRI-Scout'
    
    return LaunchDescription([
       # 1. ACTIVATE RETINA (USB V4L2 Camera)
        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            name='v4l2_camera_node',
            output='screen', # Change to 'screen' temporarily to see errors
            parameters=[{
                'image_size': [320, 240], 
                'time_per_frame': [1, 10], # Increased to 10 FPS, Pi handles MJPG easily
                'pixel_format': 'mjpeg',   # THE MAGIC: Pulls hardware block [2] from camera
            }]
        ),
        
        # 2. ACTIVATE FRONT SHIELD (LiDAR)
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
            output='screen', # Essential to read target logs
            emulate_tty=True
        )
    ])