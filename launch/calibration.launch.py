import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    # Absolute path to scripts directory (Pi user workspace)
    base_dir = '/home/ubuntu/AGRI-Scout'
    
    return LaunchDescription([
        # 1. Launch LiDAR natively as a ROS 2 Node
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar_node',
            output='log', # Avoid polluting the screen with Lidar messages
            parameters=[{
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 115200,
                'frame_id': 'laser',
                'angle_compensate': True,
                'scan_mode': 'Standard'
            }]
        ),
        
        # 2. Run pure Python script for IMU Artemis in the background
        ExecuteProcess(
            cmd=['python3', 'python_control/imu_artemis_parser.py'],
            cwd=base_dir,
            output='screen', # Show Roll, Pitch, and Yaw on main screen
            emulate_tty=True # Keep print output formatted perfectly
        )
    ])
